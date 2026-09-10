"""
Evaluation utilities: lead-time computation and slice metrics.

Lead time = for each test user who actually spirals,
  model_warned_month (earliest t where P(spiral) >= 0.5)
  minus spiral_confirmed_month (from loop detector).
  Lead time = confirmed - warned (in months).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from backend.app.services.features import FEATURE_NAMES
from backend.app.services.loop_detector import find_spiral_month


def _predict_calibrated(model, calibrator, X):
    """Get calibrated probabilities: model -> raw probs -> isotonic calibrator."""
    raw_probs = model.predict_proba(X)[:, 1]
    return calibrator.predict(raw_probs)


def compute_lead_times(
    model,
    calibrator,
    test_df: pd.DataFrame,
    raw_df: pd.DataFrame,
    feature_names: list[str],
    threshold: float = 0.5,
) -> list[float]:
    """
    For each test user who actually enters a spiral (loop detector fires),
    compute lead_time = spiral_confirmed_month - model_warned_month.

    model_warned_month = earliest prediction origin where calibrated P >= threshold.
    spiral_confirmed_month = first month where loop detector fires.
    """
    lead_times = []
    test_users = test_df["user_id"].unique()

    for uid in test_users:
        user_raw = raw_df[raw_df["user_id"] == uid].to_dict("records")
        spiral_month = find_spiral_month(user_raw)

        if spiral_month is None:
            continue

        user_test = test_df[test_df["user_id"] == uid].sort_values("as_of")

        warned_month = None
        for _, row in user_test.iterrows():
            X = row[feature_names].values.reshape(1, -1)
            prob = _predict_calibrated(model, calibrator, X)
            if prob[0] >= threshold:
                warned_month = int(row["as_of"])
                break

        if warned_month is not None and warned_month < spiral_month:
            lead_time = spiral_month - warned_month
            lead_times.append(float(lead_time))

    return lead_times


def compute_fp_rate_recovering(
    model,
    calibrator,
    test_df: pd.DataFrame,
    feature_names: list[str],
    threshold: float = 0.5,
) -> float:
    """FP rate on the recovering cohort slice: fraction predicted positive who are actually negative."""
    recovering = test_df[test_df["cohort"] == "recovering"]
    if len(recovering) == 0:
        return 0.0

    X = recovering[feature_names].values
    y = recovering["y"].values

    probs = _predict_calibrated(model, calibrator, X)
    y_pred = (probs >= threshold).astype(int)

    negatives = (y == 0)
    if negatives.sum() == 0:
        return 0.0

    fp = ((y_pred == 1) & (y == 0)).sum()
    return float(fp / negatives.sum())
