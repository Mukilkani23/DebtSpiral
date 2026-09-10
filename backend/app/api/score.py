from fastapi import APIRouter, HTTPException
from ..schemas import ScoreRequest, ScoreResponse, RiskBand, ShapExplanation, ShapItem
from ..services.session_store import get_persona
from ..services import features as feature_engine
from ..services import scoring
from ..services import explain as shap_engine
from ..services.loop_detector import evaluate as loop_evaluate, find_spiral_month

router = APIRouter()


def _band(score: int) -> RiskBand:
    if score >= 70: return RiskBand.HIGH
    if score >= 50: return RiskBand.ELEVATED
    if score >= 30: return RiskBand.MODERATE
    return RiskBand.LOW


def compute_full_score(persona, as_of: int | None = None):
    history = [s.model_dump() for s in persona.history]
    if as_of is None:
        as_of = max(s["month_index"] for s in history)

    history_up_to = [s for s in history if s["month_index"] <= as_of]
    feats = feature_engine.build(history_up_to, as_of=as_of)
    prob, risk_score = scoring.predict(feats)
    spiral = loop_evaluate(history, at_month=as_of)
    spiral_month = find_spiral_month(history)

    model = scoring.get_booster()
    shap_data = shap_engine.explain(feats, model)

    warned = None
    if spiral_month:
        for t in range(6, spiral_month + 1):
            h_t = [s for s in history if s["month_index"] <= t]
            if len(h_t) >= 4:
                f_t = feature_engine.build(h_t, as_of=t)
                p_t, s_t = scoring.predict(f_t)
                if s_t >= 50:
                    warned = t
                    break

    lead = float(spiral_month - warned) if (spiral_month and warned and warned < spiral_month) else None

    return {
        "risk_score": risk_score,
        "probability": round(prob, 4),
        "band": _band(risk_score),
        "spiral_detected": spiral,
        "spiral_confirmed_month": spiral_month,
        "model_warned_month": warned,
        "lead_time_months": lead,
        "features": feats,
        "shap": shap_data,
    }


@router.post("/score", response_model=ScoreResponse)
def compute_score(req: ScoreRequest):
    persona = get_persona(req.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    result = compute_full_score(persona, req.as_of_month)

    shap_resp = ShapExplanation(
        base_value=result["shap"]["base_value"],
        items=[ShapItem(**item) for item in result["shap"]["items"]],
    ) if result["shap"] else None

    return ScoreResponse(
        risk_score=result["risk_score"],
        probability=result["probability"],
        band=result["band"],
        spiral_detected=result["spiral_detected"],
        spiral_confirmed_month=result["spiral_confirmed_month"],
        model_warned_month=result["model_warned_month"],
        lead_time_months=result["lead_time_months"],
        features_summary={k: round(v, 4) for k, v in result["features"].items()},
        shap=shap_resp,
    )
