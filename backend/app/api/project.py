from fastapi import APIRouter, HTTPException
from ..schemas import (
    ProjectionRequest, ProjectionResponse,
    ProjectionScenario, CostOfNextDecision,
)
from ..services.session_store import get_persona
from ..services.projection import project

router = APIRouter()


@router.post("/project", response_model=ProjectionResponse)
def project_scenarios(req: ProjectionRequest):
    persona = get_persona(req.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    result = project(persona, req.levers.model_dump())

    return ProjectionResponse(
        horizon_months=result["horizon_months"],
        scenario_a=ProjectionScenario(**result["scenario_a"]),
        scenario_b=ProjectionScenario(**result["scenario_b"]),
        difference_inr=result["difference_inr"],
        cost_of_next_decision=CostOfNextDecision(**result["cost_of_next_decision"]),
    )
