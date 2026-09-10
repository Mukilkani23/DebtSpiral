from fastapi import APIRouter, HTTPException
from ..schemas import TransactionRequest, TransactionResponse, RiskBand
from ..services.session_store import get_persona

router = APIRouter()


@router.post("/transaction", response_model=TransactionResponse)
def process_transaction(req: TransactionRequest):
    persona = get_persona(req.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    if not persona.is_live:
        raise HTTPException(status_code=403, detail="Persona is not live — static snapshot only")
    return TransactionResponse(
        flagged=False,
        risk_score=0,
        risk_before=0,
        probability=0.0,
        band=RiskBand.LOW,
        spiral_detected=False,
        reason_codes=[],
        shap=None,
        nudge=None,
        nudge_triggered=False,
    )
