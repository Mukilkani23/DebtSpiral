"""
Extra-funds allocation engine. Deterministic, tier-aware, explainable.
PURE: no I/O, no globals, no config reads — ratios are passed in explicitly.
"""


def allocate(
    extra_amount: float,
    extra_funds_ratios: dict[str, float],
    risk_band: str,
    spiral_detected: bool,
) -> dict:
    """
    Split extra_amount across Tier 1/2/3 using extra_funds_ratios (keys "1","2","3",
    must sum to ~1.0). When the persona is spiraling or in an elevated/high risk band,
    shift half of the Tier 3 share onto Tier 1 as a conservative adjustment.

    Returns exact totals summing to extra_amount (rounding remainder folds into Tier 1).
    """
    ratios = {k: float(v) for k, v in extra_funds_ratios.items()}

    conservative = spiral_detected or risk_band in ("HIGH", "ELEVATED")
    if conservative:
        shift = ratios.get("3", 0.0) * 0.5
        ratios = {
            "1": ratios.get("1", 0.0) + shift,
            "2": ratios.get("2", 0.0),
            "3": ratios.get("3", 0.0) - shift,
        }

    amounts = {tier: round(extra_amount * ratio) for tier, ratio in ratios.items()}
    remainder = round(extra_amount - sum(amounts.values()))
    amounts["1"] = amounts.get("1", 0) + remainder

    reasons = {
        "1": (
            "Your Tier 1 essentials get extra priority because your trajectory is deteriorating."
            if conservative else
            "Covers essential obligations first, per your configured Tier 1 priority."
        ),
        "2": "Stays within your configured Tier 2 discretionary allocation.",
        "3": (
            "Tier 3 restricted further to avoid worsening your trajectory."
            if conservative else
            "Kept within your configured Tier 3 restricted reserve."
        ),
    }

    allocation = [
        {"tier": 1, "amount": float(amounts.get("1", 0)), "reason": reasons["1"]},
        {"tier": 2, "amount": float(amounts.get("2", 0)), "reason": reasons["2"]},
        {"tier": 3, "amount": float(amounts.get("3", 0)), "reason": reasons["3"]},
    ]

    suggestion = (
        f"Use the additional ₹{extra_amount:,.0f} primarily for Tier 1 essentials "
        f"(₹{amounts.get('1', 0):,.0f}) and planned Tier 2 spending (₹{amounts.get('2', 0):,.0f}). "
        f"Keep Tier 3 spending restricted (₹{amounts.get('3', 0):,.0f})."
    )

    return {
        "extra_amount": extra_amount,
        "allocation": allocation,
        "priority_order": [1, 2, 3],
        "suggestion": suggestion,
    }
