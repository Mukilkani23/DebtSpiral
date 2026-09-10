"""
Transaction rule engine. Deterministic, event-level flags + reason codes.
PURE: no I/O, no globals, no config reads.
Never imports explain.py. Never uses SHAP values.
"""

from dataclasses import dataclass

ALTERNATIVES = {
    "food_delivery": "Home-cooked meal, ~₹250 — ₹1,750 saved",
    "shopping": "Delay purchase 7 days — impulse fades for 70% of buyers",
    "entertainment": "Free alternatives: parks, library, community events",
    "travel": "Compare prices or postpone to off-peak for 30-40% savings",
    "electronics": "Wait for sale season or buy refurbished — 20-50% savings",
    "subscription": "Review and cancel unused subscriptions",
    "other": "Consider whether this purchase is necessary right now",
}


@dataclass
class RuleResult:
    flagged: bool
    reason_codes: list[dict]
    suggested_alternative: str
    nudge_message: str


def evaluate(
    category: str,
    amount: float,
    tier: int,
    monthly_income: float,
    utilization_level: float,
    stc_frequency: float,
    recovery_capacity: float,
    risk_score: int,
    risk_band: str,
    spiral_detected: bool,
    budget_spent: float,
    budget_limit: float,
) -> RuleResult:
    codes = []

    if tier >= 2:
        codes.append({
            "code": "TIER_2",
            "label": "Discretionary spend",
            "detail": f"Category '{category}' is Tier {tier} (discretionary)",
            "severity": 1,
        })

    if amount > 0.03 * monthly_income:
        pct = round(amount / monthly_income * 100, 1)
        codes.append({
            "code": "LARGE_RELATIVE_TXN",
            "label": "Large vs your income",
            "detail": f"₹{amount:,.0f} is {pct}% of monthly income ₹{monthly_income:,.0f}",
            "severity": 2,
        })

    if budget_limit > 0 and (budget_spent + amount) > budget_limit:
        over = budget_spent + amount - budget_limit
        codes.append({
            "code": "BUDGET_EXCEEDED",
            "label": "Past your category budget",
            "detail": f"After this: ₹{budget_spent + amount:,.0f} / ₹{budget_limit:,.0f} (over by ₹{over:,.0f})",
            "severity": 2,
        })

    if utilization_level > 0.60:
        codes.append({
            "code": "HIGH_UTILIZATION",
            "label": "Credit already stretched",
            "detail": f"Utilization {utilization_level*100:.0f}% — above the 60% threshold",
            "severity": 3,
        })

    if stc_frequency >= 1:
        codes.append({
            "code": "RECENT_SHORT_TERM_CREDIT",
            "label": "Borrowed recently",
            "detail": f"Short-term credit frequency: {stc_frequency:.1f}/month over recent window",
            "severity": 3,
        })

    if recovery_capacity < 0.05:
        codes.append({
            "code": "LOW_RECOVERY_CAPACITY",
            "label": "Little room to recover",
            "detail": f"Recovery capacity: {recovery_capacity:.3f} (below 0.05 threshold)",
            "severity": 3,
        })

    if spiral_detected:
        codes.append({
            "code": "SPIRAL_TRAJECTORY",
            "label": "Trajectory already deteriorating",
            "detail": "Loop detector has confirmed an active debt spiral",
            "severity": 3,
        })

    if risk_score >= 60:
        codes.append({
            "code": "ELEVATED_RISK_BAND",
            "label": "Model risk elevated",
            "detail": f"Risk score {risk_score} (band: {risk_band})",
            "severity": 2,
        })

    has_tier_2 = any(c["code"] == "TIER_2" for c in codes)
    other_severity = sum(c["severity"] for c in codes if c["code"] != "TIER_2")
    flagged = has_tier_2 and other_severity >= 4

    codes.sort(key=lambda c: c["severity"], reverse=True)
    codes = codes[:4]

    alt = ALTERNATIVES.get(category, ALTERNATIVES["other"])

    if flagged:
        msg = f"DebtSpiral Alert: Your ₹{amount:,.0f} {category.replace('_', ' ')} payment exceeds your budget and increases risk. Consider: {alt}"
    else:
        msg = ""

    return RuleResult(
        flagged=flagged,
        reason_codes=codes,
        suggested_alternative=alt,
        nudge_message=msg,
    )
