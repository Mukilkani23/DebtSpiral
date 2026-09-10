"""
Deterministic spiral detector. PRESENT TENSE, backward-looking.
"You ARE in a spiral." Uses months t-3..t.
PURE: no I/O, no globals, no config reads.
"""

from dataclasses import dataclass


@dataclass
class SnapshotMetrics:
    month_index: int
    utilization: float
    dti: float
    min_payment_ratio: float
    stc_frequency: float
    recovery_capacity: float


def extract_metrics(snapshot: dict) -> SnapshotMetrics:
    debt = snapshot["outstanding_debt_inr"]
    credit_limit = snapshot["credit_limit_inr"]
    income = snapshot["income_inr"]
    emi = snapshot["emi_obligations_inr"]
    essentials = snapshot["essential_spend_inr"]
    repayment = snapshot["repayment_inr"]
    min_due = snapshot["min_due_inr"]
    stc_count = snapshot["short_term_credit_count"]

    utilization = debt / max(credit_limit, 1)
    dti = (debt + emi * 12) / max(income * 12, 1)
    min_payment_ratio = repayment / max(min_due, 1)
    min_payment_ratio = min(min_payment_ratio, 3.0)
    recovery_capacity = (income - essentials - emi) / max(debt, 1)

    return SnapshotMetrics(
        month_index=snapshot["month_index"],
        utilization=utilization,
        dti=dti,
        min_payment_ratio=min_payment_ratio,
        stc_frequency=float(stc_count),
        recovery_capacity=recovery_capacity,
    )


def _is_deteriorating(curr: SnapshotMetrics, prev: SnapshotMetrics) -> bool:
    return (
        curr.utilization > prev.utilization
        or curr.min_payment_ratio < prev.min_payment_ratio
    )


def evaluate(history: list[dict], at_month: int | None = None) -> bool:
    """
    Evaluate whether the user IS in a spiral at `at_month`.
    Uses months [at_month-3 .. at_month].

    history: list of snapshot dicts with month_index keys.
    at_month: the month to evaluate at. Defaults to the last month in history.

    Returns True if all three conditions are met:
      COND_1: deteriorating() true for 3+ consecutive months ending at t
      COND_2: ≥2 of {utilization, dti, min_payment_ratio, stc_frequency}
              strictly worse at t than at t-3
      COND_3: recovery_capacity_t ≤ recovery_capacity_{t-3}
    """
    by_month = {s["month_index"]: s for s in history}

    if at_month is None:
        at_month = max(by_month.keys())

    required_months = [at_month - 3, at_month - 2, at_month - 1, at_month]
    if any(m not in by_month for m in required_months):
        return False

    metrics = [extract_metrics(by_month[m]) for m in required_months]
    t_minus_3, t_minus_2, t_minus_1, t_now = metrics

    consecutive_deterioration = 0
    pairs = [(t_minus_3, t_minus_2), (t_minus_2, t_minus_1), (t_minus_1, t_now)]
    for prev, curr in pairs:
        if _is_deteriorating(curr, prev):
            consecutive_deterioration += 1
        else:
            consecutive_deterioration = 0

    cond_1 = consecutive_deterioration >= 3

    worse_count = 0
    if t_now.utilization > t_minus_3.utilization:
        worse_count += 1
    if t_now.dti > t_minus_3.dti:
        worse_count += 1
    if t_now.min_payment_ratio < t_minus_3.min_payment_ratio:
        worse_count += 1
    if t_now.stc_frequency > t_minus_3.stc_frequency:
        worse_count += 1

    cond_2 = worse_count >= 2

    cond_3 = t_now.recovery_capacity <= t_minus_3.recovery_capacity

    return cond_1 and cond_2 and cond_3


def find_spiral_month(history: list[dict]) -> int | None:
    """Find the earliest month where the spiral detector fires."""
    by_month = {s["month_index"]: s for s in history}
    months = sorted(by_month.keys())

    for m in months:
        if m >= 4 and evaluate(history, at_month=m):
            return m
    return None
