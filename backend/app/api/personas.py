from fastapi import APIRouter, HTTPException
from ..schemas import PersonaSummary, PersonaDetailResponse, RiskAssessment, ShapExplanation, ShapItem
from ..services.session_store import get_all_personas, get_persona
from .score import compute_full_score

router = APIRouter()


@router.get("/personas", response_model=list[PersonaSummary])
def list_personas():
    personas = get_all_personas()
    results = []
    for p in personas:
        try:
            score_data = compute_full_score(p)
            results.append(PersonaSummary(
                persona_id=p.persona_id,
                label=p.label,
                monthly_income_inr=p.monthly_income_inr,
                income_type=p.income_type,
                credit_limit_inr=p.credit_limit_inr,
                is_live=p.is_live,
                narrative=p.narrative,
                current_risk_score=score_data["risk_score"],
                spiral_detected=score_data["spiral_detected"],
            ))
        except Exception:
            results.append(PersonaSummary(
                persona_id=p.persona_id,
                label=p.label,
                monthly_income_inr=p.monthly_income_inr,
                income_type=p.income_type,
                credit_limit_inr=p.credit_limit_inr,
                is_live=p.is_live,
                narrative=p.narrative,
                current_risk_score=0,
                spiral_detected=False,
            ))
    return results


@router.get("/personas/{persona_id}", response_model=PersonaDetailResponse)
def get_persona_detail(persona_id: str):
    persona = get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    result = compute_full_score(persona)

    assessment = RiskAssessment(
        risk_score=result["risk_score"],
        probability=result["probability"],
        band=result["band"],
        spiral_detected=result["spiral_detected"],
        spiral_confirmed_month=result["spiral_confirmed_month"],
        model_warned_month=result["model_warned_month"],
        lead_time_months=result["lead_time_months"],
    )

    shap_resp = ShapExplanation(
        base_value=result["shap"]["base_value"],
        items=[ShapItem(**item) for item in result["shap"]["items"]],
    ) if result["shap"] else None

    return PersonaDetailResponse(
        persona=persona,
        assessment=assessment,
        shap=shap_resp,
    )
