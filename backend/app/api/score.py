from fastapi import APIRouter, HTTPException
from ..schemas import ScoreRequest, ScoreResponse, RiskBand
from ..services.session_store import get_persona

router = APIRouter()


@router.post("/score", response_model=ScoreResponse)
def compute_score(req: ScoreRequest):
    persona = get_persona(req.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return ScoreResponse(
        risk_score=0,
        probability=0.0,
        band=RiskBand.LOW,
        spiral_detected=False,
    )
