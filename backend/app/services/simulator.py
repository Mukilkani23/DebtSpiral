"""
Shared month-stepper for both data generation and projection engine.
PURE: no I/O, no globals, no config reads.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class SimulatorParams:
    income_base: float
    income_volatility: float
    discretionary_share: float
    repayment_discipline: float
    borrow_propensity: float
    credit_limit: float
    emi_obligations: float
    apr: float = 0.36
    essential_share: float = 0.42
    shock_probability: float = 0.06
    shock_min_multiplier: float = 0.5
    shock_max_multiplier: float = 2.0


@dataclass
class MonthState:
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


def compute_min_due(debt: float, apr: float) -> float:
    interest = (apr / 12) * debt
    principal_component = max(debt * 0.01, 500)
    return max(round(interest + principal_component, 2), 0)


def step_month(
    params: SimulatorParams,
    prev_debt: float,
    month_index: int,
    rng: np.random.Generator,
    discretionary_override: float | None = None,
    repayment_discipline_override: float | None = None,
    borrow_propensity_override: float | None = None,
    force_shock: float | None = None,
    spike_amount: float = 0.0,
) -> MonthState:
    """
    Simulate one month. Returns the state snapshot for that month.

    discretionary_override, repayment_discipline_override, borrow_propensity_override
    allow the projection engine to vary behavioral parameters while keeping
    the same step logic.

    force_shock: if set, overrides stochastic shock with this exact amount.
    spike_amount: additional discretionary spend (e.g. from a specific transaction).
    """
    income = params.income_base * (1 + rng.normal(0, params.income_volatility))
    income = max(income, params.income_base * 0.3)

    essentials = params.essential_share * params.income_base * (1 + rng.normal(0, 0.03))
    essentials = max(essentials, 0)

    disc_share = discretionary_override if discretionary_override is not None else params.discretionary_share
    discretionary = disc_share * income + spike_amount
    discretionary = max(discretionary, 0)

    if force_shock is not None:
        shock = force_shock
    elif rng.random() < params.shock_probability:
        shock = params.income_base * rng.uniform(
            params.shock_min_multiplier, params.shock_max_multiplier
        )
    else:
        shock = 0.0

    emi = params.emi_obligations

    min_due = compute_min_due(prev_debt, params.apr)

    free_cash = income - essentials - emi - discretionary - shock

    discipline = (
        repayment_discipline_override
        if repayment_discipline_override is not None
        else params.repayment_discipline
    )
    repayment = min_due + discipline * max(free_cash, 0)
    repayment = max(repayment, 0)
    repayment = min(repayment, prev_debt + min_due)

    borrow_prop = (
        borrow_propensity_override
        if borrow_propensity_override is not None
        else params.borrow_propensity
    )

    if free_cash < 0:
        shortfall = abs(free_cash)
        borrowed = shortfall * borrow_prop
        stc_count = 1 if borrowed > 0 else 0
        stc_amount = borrowed
    else:
        borrowed = 0.0
        stc_count = 0
        stc_amount = 0.0

    interest = (params.apr / 12) * prev_debt
    new_debt = prev_debt + borrowed + interest - repayment
    new_debt = max(new_debt, 0)

    return MonthState(
        month_index=month_index,
        income_inr=round(income, 2),
        essential_spend_inr=round(essentials, 2),
        discretionary_spend_inr=round(discretionary, 2),
        outstanding_debt_inr=round(new_debt, 2),
        credit_limit_inr=params.credit_limit,
        repayment_inr=round(repayment, 2),
        min_due_inr=round(min_due, 2),
        short_term_credit_count=stc_count,
        short_term_credit_amount_inr=round(stc_amount, 2),
        emi_obligations_inr=emi,
    )


def simulate_trajectory(
    params: SimulatorParams,
    initial_debt: float,
    n_months: int,
    rng: np.random.Generator,
    discipline_shift_month: int | None = None,
    discipline_shift_target: float | None = None,
    discretionary_decay_rate: float = 0.0,
    borrow_growth_rate: float = 0.0,
    forced_shocks: dict[int, float] | None = None,
) -> list[MonthState]:
    """
    Simulate n_months of financial trajectory.

    discipline_shift_month: month at which repayment_discipline jumps
        (for recovering users).
    discipline_shift_target: new discipline value after the shift.
    discretionary_decay_rate: per-month additive increase to discretionary_share
        (for entering-spiral users).
    borrow_growth_rate: per-month additive increase to borrow_propensity
        (for entering-spiral users).
    forced_shocks: {month_index: shock_amount} for temporary-emergency users.
    """
    states: list[MonthState] = []
    debt = initial_debt
    current_discipline = params.repayment_discipline
    current_disc_share = params.discretionary_share
    current_borrow = params.borrow_propensity

    for m in range(1, n_months + 1):
        if discipline_shift_month is not None and m >= discipline_shift_month:
            if discipline_shift_target is not None:
                current_discipline = discipline_shift_target
            current_disc_share = max(
                current_disc_share - discretionary_decay_rate, 0.08
            )
            current_borrow = max(current_borrow - borrow_growth_rate, 0.0)
        else:
            current_disc_share = min(
                params.discretionary_share + discretionary_decay_rate * (m - 1),
                0.70,
            )
            current_borrow = min(
                params.borrow_propensity + borrow_growth_rate * (m - 1),
                0.95,
            )

        shock = None
        if forced_shocks and m in forced_shocks:
            shock = forced_shocks[m]

        state = step_month(
            params=params,
            prev_debt=debt,
            month_index=m,
            rng=rng,
            discretionary_override=current_disc_share,
            repayment_discipline_override=current_discipline,
            borrow_propensity_override=current_borrow,
            force_shock=shock,
        )
        states.append(state)
        debt = state.outstanding_debt_inr

    return states


def add_observation_noise(
    states: list[MonthState], rng: np.random.Generator, noise_pct: float = 0.06
) -> list[MonthState]:
    """Add ±noise_pct observation noise to reported aggregates."""
    noisy = []
    for s in states:
        factor = lambda: 1 + rng.uniform(-noise_pct, noise_pct)
        noisy.append(MonthState(
            month_index=s.month_index,
            income_inr=round(s.income_inr * factor(), 2),
            essential_spend_inr=round(s.essential_spend_inr * factor(), 2),
            discretionary_spend_inr=round(s.discretionary_spend_inr * factor(), 2),
            outstanding_debt_inr=round(s.outstanding_debt_inr * factor(), 2),
            credit_limit_inr=s.credit_limit_inr,
            repayment_inr=round(s.repayment_inr * factor(), 2),
            min_due_inr=round(s.min_due_inr * factor(), 2),
            short_term_credit_count=s.short_term_credit_count,
            short_term_credit_amount_inr=round(s.short_term_credit_amount_inr * factor(), 2),
            emi_obligations_inr=s.emi_obligations_inr,
        ))
    return noisy
