import time
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from ..config import settings, START_TIME
from ..schemas import HealthResponse, DemoAccountResponse, AccountAdjustRequest
from ..services.session_store import reset_all, get_all_personas, get_persona
from ..services.scoring import is_loaded, get_trained_at
from ..services.notify import reset as reset_notify, send as notify_send
from ..services import account_store, tier_config_store
from ..services import allocation as allocation_engine
from .score import compute_full_score

router = APIRouter()


@router.post("/reset")
def reset_demo():
    reset_all()
    reset_notify()
    account_store.reset_all()
    tier_config_store.reset()
    return {"status": "ok"}


@router.get("/admin/account", response_model=DemoAccountResponse)
def get_demo_account(persona_id: str):
    if not get_persona(persona_id):
        raise HTTPException(status_code=404, detail="Persona not found")
    account = account_store.get_account(persona_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found for persona")
    return DemoAccountResponse(**account)


@router.post("/admin/account/adjust", response_model=DemoAccountResponse)
def adjust_demo_account(req: AccountAdjustRequest, background_tasks: BackgroundTasks):
    persona = get_persona(req.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    try:
        account = account_store.adjust_balance(req.persona_id, req.amount)
    except KeyError:
        raise HTTPException(status_code=404, detail="Account not found for persona")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if req.amount > 0:
        score_data = compute_full_score(persona)
        tier_config = tier_config_store.get_config()
        result = allocation_engine.allocate(
            extra_amount=req.amount,
            extra_funds_ratios=tier_config["extra_funds_ratios"],
            risk_band=score_data["band"].value,
            spiral_detected=score_data["spiral_detected"],
        )
        account_store.record_allocation(req.persona_id, result)
        account = account_store.get_account(req.persona_id)

        message = (
            f"You received an extra ₹{req.amount:,.0f}.\n\n"
            f"Suggested plan:\n"
            + "\n".join(
                f"₹{item['amount']:,.0f} -> Tier {item['tier']}: {item['reason']}"
                for item in result["allocation"]
            )
            + "\n\nThis is a recommendation only — no payment has been made."
        )
        background_tasks.add_task(
            notify_send,
            nudge_id=str(uuid.uuid4()),
            message=message,
            twilio_enabled=settings.twilio_enabled,
            twilio_sid=settings.twilio_account_sid,
            twilio_token=settings.twilio_auth_token,
            twilio_from=settings.twilio_whatsapp_from,
            twilio_to=settings.demo_whatsapp_to,
            timeout=settings.notify_timeout_s,
        )

    return DemoAccountResponse(**account)


@router.get("/health", response_model=HealthResponse)
def health_check():
    personas = get_all_personas()
    return HealthResponse(
        status="ok",
        model_loaded=is_loaded(),
        model_trained_at=get_trained_at(),
        personas_loaded=len(personas),
        twilio_configured=settings.twilio_enabled,
        uptime_s=round(time.time() - START_TIME, 1),
    )
