import uuid
import statistics
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from ..config import settings
from ..schemas import (
    TransactionRequest, TransactionResponse, RiskBand,
    ReasonCode, ShapExplanation, ShapItem, NudgeResponse, DeliveryStatus,
    InsufficientBalanceResponse,
)
from ..services.session_store import get_persona, update_persona
from ..services import features as feature_engine
from ..services import scoring
from ..services import explain as shap_engine
from ..services.loop_detector import evaluate as loop_evaluate, find_spiral_month
from ..services.rules import evaluate as rules_evaluate
from ..services.notify import send as notify_send
from ..services import tier_config_store
from ..services import account_store
from ..services import category_spend_store
from ..services import message_builder
from .score import _band

router = APIRouter()


@router.post("/transaction", response_model=TransactionResponse)
def process_transaction(req: TransactionRequest, background_tasks: BackgroundTasks):
    persona = get_persona(req.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    if not persona.is_live:
        raise HTTPException(status_code=403, detail="Persona is not live — static snapshot only")

    # Financial-account validation happens BEFORE any state mutation or risk
    # pipeline work. account_store.adjust_balance() checks-and-commits in one
    # call (no separate read-then-write), so a rejection here touches nothing
    # else: no persona.history mutation, no scoring, no rule engine, no nudge.
    try:
        account_store.adjust_balance(req.persona_id, -req.amount_inr)
    except KeyError:
        raise HTTPException(status_code=404, detail="Account not found for persona")
    except ValueError:
        account = account_store.get_account(req.persona_id)
        available = account["balance_inr"] if account else 0.0
        shortfall = round(req.amount_inr - available, 2)
        error = InsufficientBalanceResponse(
            requested_amount_inr=req.amount_inr,
            available_balance_inr=available,
            shortfall_inr=shortfall,
        )
        return JSONResponse(status_code=400, content=error.model_dump())

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

    # Person-specific notification context: derived entirely from this
    # persona's actual tier config + category spend history — never a
    # single hardcoded message. Read PRIOR state before recording this
    # transaction, since is_new_category/anomaly compare against history
    # that must not include the transaction currently being evaluated.
    category_budget = tier_config_store.get_budget(req.category.value)
    prior_spend = category_spend_store.get_spend(req.persona_id, req.category.value)
    amount_history = category_spend_store.get_amount_history(req.persona_id, req.category.value)
    is_new_category = category_spend_store.is_new_category(req.persona_id, req.category.value)

    is_amount_anomaly = False
    if len(amount_history) >= 2:
        mean = statistics.mean(amount_history)
        std = statistics.pstdev(amount_history)
        if std > 0 and req.amount_inr > mean + 2 * std:
            is_amount_anomaly = True

    spent_after = prior_spend + req.amount_inr
    overage = max(spent_after - category_budget, 0) if category_budget > 0 else 0
    remaining = max(category_budget - spent_after, 0) if category_budget > 0 else 0

    notif_context = {
        "category": req.category.value,
        "tier": tier,
        "transaction_amount_inr": req.amount_inr,
        "allocated_amount_inr": category_budget,
        "spent_amount_inr": spent_after,
        "remaining_amount_inr": remaining,
        "overage_amount_inr": overage,
        "is_new_category": is_new_category,
        "is_amount_anomaly": is_amount_anomaly,
    }
    notif_result = message_builder.build_message(notif_context)
    category_spend_store.record(req.persona_id, req.category.value, req.amount_inr)

    nudge_resp = None
    # A category-budget-specific event (e.g. TIER_BUDGET_EXCEEDED,
    # UNPLANNED_EXPENSE) is an independent signal from the rule engine's
    # flagged decision — it can trigger a nudge even when rules.py alone
    # would not have flagged this transaction.
    nudge_triggered = rule_result.flagged or notif_result["event_type"] != "GENERIC"

    if nudge_triggered:
        nid = str(uuid.uuid4())
        if notif_result["event_type"] != "GENERIC":
            # Person-specific, budget-aware message — built from this
            # persona's actual tier config and category spend, not SHAP.
            nudge_message = notif_result["message"]
        else:
            # Fall back to the existing rule-engine nudge, customized with
            # the model's top SHAP driver. Presentation-only: never touches
            # reason_codes or the flagging decision (rules.py stays pure,
            # never imports explain.py).
            nudge_message = rule_result.nudge_message
            if shap_data["items"]:
                top_driver = shap_data["items"][0]["display_name"]
                nudge_message = f"{nudge_message} Biggest driver: {top_driver}."

        nudge_resp = NudgeResponse(
            nudge_id=nid,
            message=nudge_message,
            suggested_alternative=rule_result.suggested_alternative,
            delivery=DeliveryStatus(channel="fallback", status="pending", error=None),
        )
        background_tasks.add_task(
            notify_send,
            nudge_id=nid,
            message=nudge_message,
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
