"""
Projection engine: Scenario A (do nothing) vs Scenario B (change behavior).
Uses the shared simulator and re-scores simulated futures through the real model.
"""

import numpy as np
from dataclasses import asdict
from ..services.simulator import SimulatorParams, step_month
from ..services import features as feature_engine
from ..services import scoring


def _params_from_persona(persona) -> SimulatorParams:
    h = persona.history
    last = h[-1] if h else None
    if not last:
        raise ValueError("Persona has no history")
    last_d = last.model_dump() if hasattr(last, 'model_dump') else last.__dict__

    income = persona.monthly_income_inr
    disc_avg = sum(s.discretionary_spend_inr for s in h[-3:]) / min(len(h), 3)
    ess_avg = sum(s.essential_spend_inr for s in h[-3:]) / min(len(h), 3)
    repay_avg = sum(s.repayment_inr for s in h[-3:]) / min(len(h), 3)
    min_due_avg = sum(s.min_due_inr for s in h[-3:]) / min(len(h), 3)

    discipline = (repay_avg - min_due_avg) / max(income - ess_avg - last_d.get("emi_obligations_inr", 0), 1)
    discipline = max(0.0, min(1.0, discipline))

    borrow_recent = sum(1 for s in h[-3:] if s.short_term_credit_count > 0)
    borrow_prop = min(borrow_recent / 3.0 * 0.5, 0.8)

    return SimulatorParams(
        income_base=float(income),
        income_volatility=0.03,
        discretionary_share=disc_avg / max(income, 1),
        repayment_discipline=discipline,
        borrow_propensity=borrow_prop,
        credit_limit=float(persona.credit_limit_inr),
        emi_obligations=float(last_d.get("emi_obligations_inr", 0)),
        apr=0.36,
        essential_share=ess_avg / max(float(income), 1),
        shock_probability=0.0,
    )


def _simulate_scenario(
    persona,
    params: SimulatorParams,
    n_months: int,
    disc_reduction: float = 0.0,
    repayment_increase: float = 0.0,
    stc_reduction: int = 0,
) -> dict:
    history_dicts = [s.model_dump() if hasattr(s, 'model_dump') else s.__dict__ for s in persona.history]
    last = history_dicts[-1]
    debt = last["outstanding_debt_inr"]
    base_month = last["month_index"]

    rng = np.random.default_rng(42)

    disc_share = params.discretionary_share
    if disc_reduction > 0:
        disc_share = max(0.0, disc_share - disc_reduction / max(params.income_base, 1))

    discipline = params.repayment_discipline
    if repayment_increase > 0:
        discipline = min(1.0, discipline + repayment_increase / max(params.income_base, 1))

    borrow = params.borrow_propensity
    if stc_reduction > 0:
        borrow = max(0.0, borrow - stc_reduction * 0.15)

    simulated_history = list(history_dicts)
    debts = []
    risks = []
    savings_vals = []
    cumulative_savings = 0.0

    for m in range(1, n_months + 1):
        state = step_month(
            params=params,
            prev_debt=debt,
            month_index=base_month + m,
            rng=rng,
            discretionary_override=disc_share,
            repayment_discipline_override=discipline,
            borrow_propensity_override=borrow,
        )
        state_dict = asdict(state)
        simulated_history.append(state_dict)
        debt = state.outstanding_debt_inr

        free_cash = state.income_inr - state.essential_spend_inr - state.emi_obligations_inr - state.discretionary_spend_inr - state.repayment_inr
        if free_cash > 0:
            cumulative_savings += free_cash

        if m in (3, 6, 12):
            debts.append(round(debt))
            if scoring.is_loaded():
                feats = feature_engine.build(simulated_history, as_of=base_month + m)
                _, score = scoring.predict(feats)
                risks.append(score)
            else:
                risks.append(0)
            savings_vals.append(round(max(cumulative_savings, 0)))

    while len(debts) < 3:
        debts.append(debts[-1] if debts else 0)
        risks.append(risks[-1] if risks else 0)
        savings_vals.append(savings_vals[-1] if savings_vals else 0)

    return {"debt": debts, "risk": risks, "savings": savings_vals}


def project(persona, levers: dict) -> dict:
    params = _params_from_persona(persona)

    scenario_a = _simulate_scenario(persona, params, 12)
    scenario_b = _simulate_scenario(
        persona, params, 12,
        disc_reduction=levers.get("discretionary_reduction_inr", 0),
        repayment_increase=levers.get("repayment_increase_inr", 0),
        stc_reduction=levers.get("stc_reduction_count", 0),
    )

    diff = {}
    for i, h in enumerate([3, 6, 12]):
        diff[str(h)] = round(scenario_a["debt"][i] - scenario_b["debt"][i])

    disc_only_b = _simulate_scenario(
        persona, params, 12,
        disc_reduction=levers.get("discretionary_reduction_inr", 0),
    )
    debt_avoided = scenario_a["debt"][2] - disc_only_b["debt"][2]

    return {
        "horizon_months": [3, 6, 12],
        "scenario_a": scenario_a,
        "scenario_b": scenario_b,
        "difference_inr": diff,
        "cost_of_next_decision": {
            "lever": "discretionary_reduction",
            "delta_per_month_inr": levers.get("discretionary_reduction_inr", 0),
            "debt_avoided_12mo_inr": round(max(debt_avoided, 0)),
        },
    }
