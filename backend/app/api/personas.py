from fastapi import APIRouter, HTTPException
from ..schemas import PersonaSummary, PersonaDetailResponse, RiskAssessment, RiskBand
from ..services.session_store import get_all_personas, get_persona

router = APIRouter()


def _stub_assessment() -> RiskAssessment:
    return RiskAssessment(
        risk_score=0,
        probability=0.0,
        band=RiskBand.LOW,
        spiral_detected=False,
    )


@router.get("/personas", response_model=list[PersonaSummary])
def list_personas():
    personas = get_all_personas()
    return [
        PersonaSummary(
            persona_id=p.persona_id,
            label=p.label,
            monthly_income_inr=p.monthly_income_inr,
            income_type=p.income_type,
            credit_limit_inr=p.credit_limit_inr,
            is_live=p.is_live,
            narrative=p.narrative,
            current_risk_score=0,
            spiral_detected=False,
        )
        for p in personas
    ]


@router.get("/personas/{persona_id}", response_model=PersonaDetailResponse)
def get_persona_detail(persona_id: str):
    persona = get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return PersonaDetailResponse(
        persona=persona,
        assessment=_stub_assessment(),
        shap=None,
    )
