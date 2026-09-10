from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .services.session_store import load_personas, get_all_personas
from .services.scoring import load_model
from .services import tier_config_store, account_store
from .api import admin, personas, score, transaction, project, tiers


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_personas(str(settings.resolve_path(settings.personas_path)))
    model_path = str(settings.resolve_path(settings.model_path))
    calibrator_path = str(settings.resolve_path(settings.model_path).parent / "calibrator.joblib")
    load_model(model_path, calibrator_path)
    tier_config_store.load(str(settings.resolve_path(settings.tier_config_path)))
    account_store.init_accounts(get_all_personas())
    yield


app = FastAPI(
    title="DebtSpiral API",
    description="Early detection of debt spirals",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router, tags=["admin"])
app.include_router(personas.router, tags=["personas"])
app.include_router(score.router, tags=["score"])
app.include_router(transaction.router, tags=["transaction"])
app.include_router(project.router, tags=["projection"])
app.include_router(tiers.router, tags=["tier-config"])
