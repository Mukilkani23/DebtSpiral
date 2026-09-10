from fastapi import APIRouter, HTTPException
from ..schemas import TierConfigResponse, TierConfigUpdateRequest
from ..services import tier_config_store

router = APIRouter()


@router.get("/config/tiers", response_model=TierConfigResponse)
def get_tier_config():
    return TierConfigResponse(**tier_config_store.get_config())


@router.post("/config/tiers", response_model=TierConfigResponse)
def update_tier_config(req: TierConfigUpdateRequest):
    try:
        updated = tier_config_store.update_config(
            category_tiers=req.category_tiers,
            extra_funds_ratios=req.extra_funds_ratios,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TierConfigResponse(**updated)
