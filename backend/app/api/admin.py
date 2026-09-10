import time
from fastapi import APIRouter
from ..config import settings, START_TIME
from ..schemas import HealthResponse
from ..services.session_store import reset_all, get_all_personas

router = APIRouter()


@router.post("/reset")
def reset_demo():
    reset_all()
    return {"status": "ok"}


@router.get("/health", response_model=HealthResponse)
def health_check():
    personas = get_all_personas()
    return HealthResponse(
        status="ok",
        model_loaded=False,
        model_trained_at=None,
        personas_loaded=len(personas),
        twilio_configured=settings.twilio_enabled,
        uptime_s=round(time.time() - START_TIME, 1),
    )
