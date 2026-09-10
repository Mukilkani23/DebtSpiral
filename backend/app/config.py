from pydantic_settings import BaseSettings
from pathlib import Path
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_env: str = "local"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173"
    model_path: str = "backend/models/xgb_spiral.joblib"
    personas_path: str = "backend/app/data/personas.json"
    tier_config_path: str = "backend/app/data/tier_config.json"
    random_seed: int = 42

    def resolve_path(self, rel_path: str) -> Path:
        p = Path(rel_path)
        if p.is_absolute():
            return p
        return PROJECT_ROOT / p

    risk_high_threshold: int = 70
    rule_utilization_threshold: float = 0.60
    projection_apr: float = 0.36

    twilio_enabled: bool = False
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_api_key_sid: str = ""
    twilio_api_key_secret: str = ""
    twilio_content_sid: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    demo_whatsapp_to: str = "whatsapp:+919629528495"
    notify_timeout_s: float = 3.0

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
START_TIME = time.time()
