import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from ..config import settings
from ..schemas import (
    TransactionRequest, TransactionResponse, RiskBand,
    ReasonCode, ShapExplanation, ShapItem, NudgeResponse, DeliveryStatus,
)
from ..services.session_store import get_persona, update_persona
from ..services import features as feature_engine
from ..services import scoring
from ..services import explain as shap_engine
from ..services.loop_detector import evaluate as loop_evaluate, find_spiral_month
from ..services.rules import evaluate as rules_evaluate
from ..services.notify import send as notify_send
from ..services import tier_config_store
from .score import _band

router = APIRouter()


@router.post("/transaction", response_model=TransactionResponse)
def process_transaction(req: TransactionRequest, background_tasks: BackgroundTasks):
    persona = get_persona(req.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    if not persona.is_live:
        raise HTTPException(status_code=403, detail="Persona is not live — static snapshot only")

    history_before = [s.model_dump() for s in persona.history]
    as_of_before = max(s["month_index"] for s in history_before)
    feats_before = feature_engine.build(history_before, as_of=as_of_before)
    _, risk_before = scoring.predict(feats_before)

    last_snap = history_before[-1].copy()
    last_snap["discretionary_spend_inr"] += req.amount_inr
    last_snap["outstanding_debt_inr"] += req.amount_inr

    updated_history = history_before[:-1] + [last_snap]

    feats_after = feature_engine.build(updated_history, as_of=as_of_before)
    prob_after, risk_after = scoring.predict(feats_after)
    spiral = loop_evaluate(updated_history, at_month=as_of_before)
    spiral_month = find_spiral_month(updated_history)

    model = scoring.get_booster()
    shap_data = shap_engine.explain(feats_after, model)

    tier = tier_config_store.get_tier(req.category.value)

    budget_spent = last_snap["discretionary_spend_inr"] - req.amount_inr
    budget_limit = persona.monthly_income_inr * 0.30

    recovery_cap = (last_snap["income_inr"] - last_snap["essential_spend_inr"] - last_snap["emi_obligations_inr"]) / max(last_snap["outstanding_debt_inr"], 1)

    rule_result = rules_evaluate(
        category=req.category.value,
        amount=req.amount_inr,
        tier=tier,
        monthly_income=persona.monthly_income_inr,
        utilization_level=feats_after["utilization_level"],
        stc_frequency=feats_after["stc_frequency"],
        recovery_capacity=recovery_cap,
        risk_score=risk_after,
        risk_band=_band(risk_after).value,
        spiral_detected=spiral,
        budget_spent=budget_spent,
        budget_limit=budget_limit,
    )

    from ..schemas import Persona, MonthlySnapshot
    new_history = [MonthlySnapshot(**s) for s in updated_history]
    updated_persona = persona.model_copy(update={"history": new_history})
    update_persona(updated_persona)

    nudge_resp = None
    nudge_triggered = rule_result.flagged

    if nudge_triggered:
        nid = str(uuid.uuid4())
        nudge_resp = NudgeResponse(
            nudge_id=nid,
            message=rule_result.nudge_message,
            suggested_alternative=rule_result.suggested_alternative,
            delivery=DeliveryStatus(channel="fallback", status="pending", error=None),
        )
        background_tasks.add_task(
            notify_send,
            nudge_id=nid,
            message=rule_result.nudge_message,
            twilio_enabled=settings.twilio_enabled,
            twilio_sid=settings.twilio_account_sid,
            twilio_token=settings.twilio_auth_token,
            twilio_from=settings.twilio_whatsapp_from,
            twilio_to=settings.demo_whatsapp_to,
            timeout=settings.notify_timeout_s,
            twilio_api_key_sid=settings.twilio_api_key_sid,
            twilio_api_key_secret=settings.twilio_api_key_secret,
            twilio_content_sid=settings.twilio_content_sid,
        )

    shap_resp = ShapExplanation(
        base_value=shap_data["base_value"],
        items=[ShapItem(**item) for item in shap_data["items"]],
    )

    reason_codes = [ReasonCode(**rc) for rc in rule_result.reason_codes]

    return TransactionResponse(
        flagged=rule_result.flagged,
        risk_score=risk_after,
        risk_before=risk_before,
        probability=round(prob_after, 4),
        band=_band(risk_after),
        spiral_detected=spiral,
        reason_codes=reason_codes,
        shap=shap_resp,
        nudge=nudge_resp,
        nudge_triggered=nudge_triggered,
    )
