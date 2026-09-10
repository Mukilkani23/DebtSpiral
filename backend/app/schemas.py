from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class IncomeType(str, Enum):
    stable = "stable"
    variable = "variable"


class RiskBand(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"


class TransactionCategory(str, Enum):
    food_delivery = "food_delivery"
    shopping = "shopping"
    entertainment = "entertainment"
    travel = "travel"
    electronics = "electronics"
    subscription = "subscription"
    other = "other"


class MonthlySnapshot(BaseModel):
    month_index: int
    income_inr: float
    essential_spend_inr: float
    discretionary_spend_inr: float
    outstanding_debt_inr: float
    credit_limit_inr: float
    repayment_inr: float
    min_due_inr: float
    short_term_credit_count: int
    short_term_credit_amount_inr: float
    emi_obligations_inr: float


class Persona(BaseModel):
    persona_id: str
    label: str
    monthly_income_inr: int
    income_type: IncomeType
    credit_limit_inr: int
    is_live: bool
    history: list[MonthlySnapshot]
    narrative: str


class PersonaSummary(BaseModel):
    persona_id: str
    label: str
    monthly_income_inr: int
    income_type: IncomeType
    credit_limit_inr: int
    is_live: bool
    narrative: str
    current_risk_score: int
    spiral_detected: bool


class RiskAssessment(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    probability: float
    band: RiskBand
    spiral_detected: bool
    spiral_confirmed_month: Optional[int] = None
    model_warned_month: Optional[int] = None
    lead_time_months: Optional[float] = None


class ShapItem(BaseModel):
    feature: str
    display_name: str
    value: float
    shap: float
    direction: str


class ShapExplanation(BaseModel):
    base_value: float
    items: list[ShapItem]


class ReasonCode(BaseModel):
    code: str
    label: str
    detail: str
    severity: int = Field(ge=1, le=3)


class DeliveryStatus(BaseModel):
    channel: str
    status: str
    error: Optional[str] = None


class NudgeResponse(BaseModel):
    nudge_id: str
    message: str
    suggested_alternative: str
    delivery: DeliveryStatus


# --- Request schemas (extra="forbid") ---

class ScoreRequest(BaseModel):
    model_config = {"extra": "forbid"}
    persona_id: str
    as_of_month: Optional[int] = None


class TransactionRequest(BaseModel):
    model_config = {"extra": "forbid"}
    persona_id: str
    category: TransactionCategory
    amount_inr: float = Field(gt=0, le=500000)


class ProjectionLevers(BaseModel):
    discretionary_reduction_inr: float = 0
    repayment_increase_inr: float = 0
    stc_reduction_count: int = 0


class ProjectionRequest(BaseModel):
    model_config = {"extra": "forbid"}
    persona_id: str
    direction: str = "risk"
    levers: ProjectionLevers


# --- Response schemas ---

class ScoreResponse(BaseModel):
    risk_score: int
    probability: float
    band: RiskBand
    spiral_detected: bool
    spiral_confirmed_month: Optional[int] = None
    model_warned_month: Optional[int] = None
    lead_time_months: Optional[float] = None
    features_summary: dict = {}
    shap: Optional[ShapExplanation] = None


class TransactionResponse(BaseModel):
    flagged: bool
    risk_score: int
    risk_before: int
    probability: float
    band: RiskBand
    spiral_detected: bool
    reason_codes: list[ReasonCode]
    shap: Optional[ShapExplanation] = None
    nudge: Optional[NudgeResponse] = None
    nudge_triggered: bool


class CostOfNextDecision(BaseModel):
    lever: str
    delta_per_month_inr: float
    debt_avoided_12mo_inr: float


class ProjectionScenario(BaseModel):
    debt: list[float]
    risk: list[int]
    savings: list[float]


class ProjectionResponse(BaseModel):
    horizon_months: list[int] = [3, 6, 12]
    scenario_a: ProjectionScenario
    scenario_b: ProjectionScenario
    difference_inr: dict[str, float]
    cost_of_next_decision: CostOfNextDecision


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_trained_at: Optional[str] = None
    personas_loaded: int
    twilio_configured: bool
    uptime_s: float


class PersonaDetailResponse(BaseModel):
    persona: Persona
    assessment: RiskAssessment
    shap: Optional[ShapExplanation] = None
