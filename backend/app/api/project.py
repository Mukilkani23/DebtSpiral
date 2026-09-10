from fastapi import APIRouter, HTTPException
from ..schemas import (
    ProjectionRequest,
    ProjectionResponse,
    ProjectionScenario,
    CostOfNextDecision,
)
from ..services.session_store import get_persona

router = APIRouter()


@router.post("/project", response_model=ProjectionResponse)
def project_scenarios(req: ProjectionRequest):
    persona = get_persona(req.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    stub_scenario = ProjectionScenario(debt=[0, 0, 0], risk=[0, 0, 0], savings=[0, 0, 0])
    return ProjectionResponse(
        scenario_a=stub_scenario,
        scenario_b=stub_scenario,
        difference_inr={"3": 0, "6": 0, "12": 0},
        cost_of_next_decision=CostOfNextDecision(
            lever="discretionary_reduction",
            delta_per_month_inr=0,
            debt_avoided_12mo_inr=0,
        ),
    )
