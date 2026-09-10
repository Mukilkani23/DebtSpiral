"""
Feature engine. 16 named features, all trailing windows.
PURE: no I/O, no globals, no config reads.
"""

import numpy as np

FEATURE_NAMES = [
    "utilization_level",
    "utilization_trend",
    "dti_level",
    "dti_trend",
    "min_payment_ratio",
    "min_payment_ratio_trend",
    "stc_frequency",
    "stc_amount_ratio",
    "discretionary_ratio",
    "income_volatility",
    "spending_volatility",
    "repayment_trend",
    "delta_30d_debt",
    "delta_90d_debt",
    "recovery_slope",
    "absolute_debt_inr",
]


def _ols_slope(values: list[float]) -> float:
    """OLS slope of values against [0, 1, 2, ...]."""
    n = len(values)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=float)
    y = np.array(values, dtype=float)
    x_mean = x.mean()
    y_mean = y.mean()
    denom = ((x - x_mean) ** 2).sum()
    if denom == 0:
        return 0.0
    return float(((x - x_mean) * (y - y_mean)).sum() / denom)


def _cv(values: list[float]) -> float:
    """Coefficient of variation (std/mean)."""
    if not values:
        return 0.0
    arr = np.array(values, dtype=float)
    mean = arr.mean()
    if mean == 0:
        return 0.0
    return float(arr.std() / abs(mean))


def build(history: list[dict], as_of: int) -> dict[str, float]:
    """
    Compute all 16 features from history up to and including as_of month.

    Raises ValueError if any snapshot has month_index > as_of.
    Returns a dict keyed by feature name.
    """
    for s in history:
        if s["month_index"] > as_of:
            raise ValueError(
                f"Anti-leakage violation: snapshot month {s['month_index']} > as_of {as_of}"
            )

    by_month = {s["month_index"]: s for s in history}
    months = sorted(m for m in by_month if m <= as_of)

    if not months:
        return {name: 0.0 for name in FEATURE_NAMES}

    t = months[-1]
    curr = by_month[t]

    window_6 = [by_month[m] for m in months if m >= t - 5]
    window_3 = [by_month[m] for m in months if m >= t - 2]
    window_2 = [by_month[m] for m in months if m >= t - 1]

    debt = curr["outstanding_debt_inr"]
    credit_limit = curr["credit_limit_inr"]
    income = curr["income_inr"]
    emi = curr["emi_obligations_inr"]
    essentials = curr["essential_spend_inr"]
    repayment = curr["repayment_inr"]
    min_due = curr["min_due_inr"]
    discretionary = curr["discretionary_spend_inr"]

    utilization_level = debt / max(credit_limit, 1)

    util_series = [s["outstanding_debt_inr"] / max(s["credit_limit_inr"], 1) for s in window_6]
    utilization_trend = _ols_slope(util_series)

    dti_level = (debt + emi * 12) / max(income * 12, 1)

    dti_series = [
        (s["outstanding_debt_inr"] + s["emi_obligations_inr"] * 12)
        / max(s["income_inr"] * 12, 1)
        for s in window_6
    ]
    dti_trend = _ols_slope(dti_series)

    min_payment_ratio_val = min(repayment / max(min_due, 1), 3.0)

    mpr_series = [
        min(s["repayment_inr"] / max(s["min_due_inr"], 1), 3.0) for s in window_6
    ]
    min_payment_ratio_trend = _ols_slope(mpr_series)

    stc_counts = [s["short_term_credit_count"] for s in window_6]
    stc_frequency = sum(stc_counts) / max(len(stc_counts), 1)

    stc_amounts = [s["short_term_credit_amount_inr"] for s in window_3]
    incomes_3 = [s["income_inr"] for s in window_3]
    stc_amount_ratio = sum(stc_amounts) / max(sum(incomes_3), 1)

    disc_vals = [s["discretionary_spend_inr"] for s in window_2]
    inc_vals = [s["income_inr"] for s in window_2]
    discretionary_ratio = sum(disc_vals) / max(sum(inc_vals), 1)

    income_series = [s["income_inr"] for s in window_6]
    income_volatility = _cv(income_series)

    spend_series = [
        s["essential_spend_inr"] + s["discretionary_spend_inr"] for s in window_6
    ]
    spending_volatility = _cv(spend_series)

    repay_debt_series = [
        s["repayment_inr"] / max(s["outstanding_debt_inr"], 1) for s in window_6
    ]
    repayment_trend = _ols_slope(repay_debt_series)

    if len(months) >= 2:
        prev_debt = by_month[months[-2]]["outstanding_debt_inr"]
        delta_30d_debt = (debt - prev_debt) / max(prev_debt, 1)
    else:
        delta_30d_debt = 0.0

    if len(months) >= 4:
        debt_3ago = by_month[months[-4]]["outstanding_debt_inr"] if len(months) >= 4 else debt
        idx_3 = max(0, len(months) - 4)
        debt_3ago = by_month[months[idx_3]]["outstanding_debt_inr"]
        delta_90d_debt = (debt - debt_3ago) / max(debt_3ago, 1)
    else:
        delta_90d_debt = 0.0

    recovery_series = [
        (s["income_inr"] - s["essential_spend_inr"] - s["emi_obligations_inr"])
        / max(s["outstanding_debt_inr"], 1)
        for s in window_6
    ]
    recovery_slope = _ols_slope(recovery_series)

    return {
        "utilization_level": round(utilization_level, 6),
        "utilization_trend": round(utilization_trend, 6),
        "dti_level": round(dti_level, 6),
        "dti_trend": round(dti_trend, 6),
        "min_payment_ratio": round(min_payment_ratio_val, 6),
        "min_payment_ratio_trend": round(min_payment_ratio_trend, 6),
        "stc_frequency": round(stc_frequency, 6),
        "stc_amount_ratio": round(stc_amount_ratio, 6),
        "discretionary_ratio": round(discretionary_ratio, 6),
        "income_volatility": round(income_volatility, 6),
        "spending_volatility": round(spending_volatility, 6),
        "repayment_trend": round(repayment_trend, 6),
        "delta_30d_debt": round(delta_30d_debt, 6),
        "delta_90d_debt": round(delta_90d_debt, 6),
        "recovery_slope": round(recovery_slope, 6),
        "absolute_debt_inr": round(debt, 2),
    }
