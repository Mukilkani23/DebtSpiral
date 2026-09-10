"""
Generate 800 synthetic users × 12 months → data/raw/users.parquet
Uses the shared simulator from backend/app/services/simulator.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from dataclasses import asdict
from backend.app.services.simulator import (
    SimulatorParams,
    simulate_trajectory,
    add_observation_noise,
)

SEED = 42
N_USERS = 800
N_MONTHS = 12
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "users.parquet"


COHORT_SPEC = {
    "healthy_stable": {"share": 0.25, "count": 200},
    "healthy_spikes": {"share": 0.12, "count": 96},
    "high_income_reckless": {"share": 0.08, "count": 64},
    "low_income_disciplined": {"share": 0.10, "count": 80},
    "entering_spiral": {"share": 0.18, "count": 144},
    "recovering": {"share": 0.10, "count": 80},
    "temporary_emergency": {"share": 0.09, "count": 72},
    "gig_variable": {"share": 0.08, "count": 64},
}


def _sample_income(rng: np.random.Generator, low: float, high: float) -> float:
    mu = np.log((low + high) / 2)
    sigma = 0.3
    val = rng.lognormal(mu, sigma)
    return float(np.clip(val, low, high))


def generate_cohort_healthy_stable(rng: np.random.Generator, user_id: int) -> dict:
    income = _sample_income(rng, 40000, 200000)
    return {
        "user_id": user_id,
        "cohort": "healthy_stable",
        "params": SimulatorParams(
            income_base=income,
            income_volatility=rng.uniform(0.02, 0.08),
            discretionary_share=rng.uniform(0.10, 0.22),
            repayment_discipline=rng.uniform(0.50, 1.00),
            borrow_propensity=rng.uniform(0.00, 0.15),
            credit_limit=income * rng.uniform(2.0, 4.0),
            emi_obligations=income * rng.uniform(0.05, 0.12),
        ),
        "initial_debt_ratio": rng.uniform(0.05, 0.25),
        "discretionary_decay_rate": 0.0,
        "borrow_growth_rate": 0.0,
        "discipline_shift_month": None,
        "discipline_shift_target": None,
        "forced_shocks": None,
    }


def generate_cohort_healthy_spikes(rng: np.random.Generator, user_id: int) -> dict:
    cfg = generate_cohort_healthy_stable(rng, user_id)
    cfg["cohort"] = "healthy_spikes"
    spike_months = rng.choice(range(3, 11), size=rng.integers(2, 4), replace=False)
    cfg["forced_shocks"] = {
        int(m): cfg["params"].income_base * rng.uniform(0.15, 0.35)
        for m in spike_months
    }
    return cfg


def generate_cohort_high_income_reckless(rng: np.random.Generator, user_id: int) -> dict:
    income = _sample_income(rng, 300000, 600000)
    return {
        "user_id": user_id,
        "cohort": "high_income_reckless",
        "params": SimulatorParams(
            income_base=income,
            income_volatility=rng.uniform(0.02, 0.08),
            discretionary_share=rng.uniform(0.35, 0.55),
            repayment_discipline=rng.uniform(0.02, 0.15),
            borrow_propensity=rng.uniform(0.40, 0.80),
            credit_limit=income * rng.uniform(1.8, 3.0),
            emi_obligations=income * rng.uniform(0.05, 0.10),
        ),
        "initial_debt_ratio": rng.uniform(0.35, 0.60),
        "discretionary_decay_rate": rng.uniform(0.005, 0.015),
        "borrow_growth_rate": rng.uniform(0.01, 0.03),
        "discipline_shift_month": None,
        "discipline_shift_target": None,
        "forced_shocks": None,
    }


def generate_cohort_low_income_disciplined(rng: np.random.Generator, user_id: int) -> dict:
    income = _sample_income(rng, 25000, 40000)
    return {
        "user_id": user_id,
        "cohort": "low_income_disciplined",
        "params": SimulatorParams(
            income_base=income,
            income_volatility=rng.uniform(0.02, 0.10),
            discretionary_share=rng.uniform(0.10, 0.18),
            repayment_discipline=rng.uniform(0.80, 1.00),
            borrow_propensity=rng.uniform(0.00, 0.10),
            credit_limit=income * rng.uniform(1.5, 3.0),
            emi_obligations=income * rng.uniform(0.08, 0.15),
        ),
        "initial_debt_ratio": rng.uniform(0.10, 0.35),
        "discretionary_decay_rate": 0.0,
        "borrow_growth_rate": 0.0,
        "discipline_shift_month": None,
        "discipline_shift_target": None,
        "forced_shocks": None,
    }


def generate_cohort_entering_spiral(rng: np.random.Generator, user_id: int) -> dict:
    income = _sample_income(rng, 35000, 120000)
    return {
        "user_id": user_id,
        "cohort": "entering_spiral",
        "params": SimulatorParams(
            income_base=income,
            income_volatility=rng.uniform(0.03, 0.12),
            discretionary_share=rng.uniform(0.20, 0.35),
            repayment_discipline=rng.uniform(0.08, 0.30),
            borrow_propensity=rng.uniform(0.35, 0.65),
            credit_limit=income * rng.uniform(1.8, 3.5),
            emi_obligations=income * rng.uniform(0.10, 0.18),
        ),
        "initial_debt_ratio": rng.uniform(0.30, 0.55),
        "discretionary_decay_rate": rng.uniform(0.015, 0.035),
        "borrow_growth_rate": rng.uniform(0.020, 0.045),
        "discipline_shift_month": None,
        "discipline_shift_target": None,
        "forced_shocks": None,
    }


def generate_cohort_recovering(rng: np.random.Generator, user_id: int) -> dict:
    cfg = generate_cohort_entering_spiral(rng, user_id)
    cfg["cohort"] = "recovering"
    cfg["discipline_shift_month"] = int(rng.integers(5, 9))
    cfg["discipline_shift_target"] = float(rng.uniform(0.65, 0.95))
    return cfg


def generate_cohort_temporary_emergency(rng: np.random.Generator, user_id: int) -> dict:
    income = _sample_income(rng, 40000, 150000)
    shock_month = int(rng.integers(5, 8))
    return {
        "user_id": user_id,
        "cohort": "temporary_emergency",
        "params": SimulatorParams(
            income_base=income,
            income_volatility=rng.uniform(0.02, 0.08),
            discretionary_share=rng.uniform(0.12, 0.25),
            repayment_discipline=rng.uniform(0.60, 0.95),
            borrow_propensity=rng.uniform(0.20, 0.50),
            credit_limit=income * rng.uniform(2.0, 4.0),
            emi_obligations=income * rng.uniform(0.05, 0.12),
        ),
        "initial_debt_ratio": rng.uniform(0.10, 0.30),
        "discretionary_decay_rate": 0.0,
        "borrow_growth_rate": 0.0,
        "discipline_shift_month": None,
        "discipline_shift_target": None,
        "forced_shocks": {
            shock_month: income * rng.uniform(0.8, 2.0),
        },
    }


def generate_cohort_gig_variable(rng: np.random.Generator, user_id: int) -> dict:
    income = _sample_income(rng, 35000, 80000)
    return {
        "user_id": user_id,
        "cohort": "gig_variable",
        "params": SimulatorParams(
            income_base=income,
            income_volatility=rng.uniform(0.30, 0.45),
            discretionary_share=rng.uniform(0.18, 0.32),
            repayment_discipline=rng.uniform(0.20, 0.55),
            borrow_propensity=rng.uniform(0.25, 0.55),
            credit_limit=income * rng.uniform(1.5, 3.0),
            emi_obligations=income * rng.uniform(0.08, 0.15),
        ),
        "initial_debt_ratio": rng.uniform(0.25, 0.50),
        "discretionary_decay_rate": 0.0,
        "borrow_growth_rate": 0.0,
        "discipline_shift_month": None,
        "discipline_shift_target": None,
        "forced_shocks": None,
    }


COHORT_GENERATORS = {
    "healthy_stable": generate_cohort_healthy_stable,
    "healthy_spikes": generate_cohort_healthy_spikes,
    "high_income_reckless": generate_cohort_high_income_reckless,
    "low_income_disciplined": generate_cohort_low_income_disciplined,
    "entering_spiral": generate_cohort_entering_spiral,
    "recovering": generate_cohort_recovering,
    "temporary_emergency": generate_cohort_temporary_emergency,
    "gig_variable": generate_cohort_gig_variable,
}


def generate_all_users(seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    all_rows = []
    user_id = 0

    for cohort_name, spec in COHORT_SPEC.items():
        gen_fn = COHORT_GENERATORS[cohort_name]
        for _ in range(spec["count"]):
            cfg = gen_fn(rng, user_id)
            params = cfg["params"]
            initial_debt = params.credit_limit * cfg["initial_debt_ratio"]

            user_rng = np.random.default_rng(rng.integers(0, 2**31))

            states = simulate_trajectory(
                params=params,
                initial_debt=initial_debt,
                n_months=N_MONTHS,
                rng=user_rng,
                discipline_shift_month=cfg["discipline_shift_month"],
                discipline_shift_target=cfg["discipline_shift_target"],
                discretionary_decay_rate=cfg["discretionary_decay_rate"],
                borrow_growth_rate=cfg["borrow_growth_rate"],
                forced_shocks=cfg["forced_shocks"],
            )

            noise_rng = np.random.default_rng(rng.integers(0, 2**31))
            states = add_observation_noise(states, noise_rng)

            for s in states:
                row = asdict(s)
                row["user_id"] = user_id
                row["cohort"] = cfg["cohort"]
                all_rows.append(row)

            user_id += 1

    df = pd.DataFrame(all_rows)
    return df


def main():
    print(f"Generating {N_USERS} users × {N_MONTHS} months...")
    df = generate_all_users()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)

    print(f"Saved to {OUTPUT_PATH}")
    print(f"Shape: {df.shape}")
    print(f"\nCohort distribution:")
    cohort_counts = df.groupby("cohort")["user_id"].nunique()
    for cohort, count in cohort_counts.items():
        print(f"  {cohort}: {count} users ({count/N_USERS*100:.1f}%)")

    print(f"\nBasic stats:")
    print(f"  Income range: {df['income_inr'].min():,.0f} - {df['income_inr'].max():,.0f}")
    print(f"  Debt range: {df['outstanding_debt_inr'].min():,.0f} - {df['outstanding_debt_inr'].max():,.0f}")
    print(f"  Any NaN: {df.isna().any().any()}")
    print(f"  Any negative debt: {(df['outstanding_debt_inr'] < 0).any()}")


if __name__ == "__main__":
    main()
