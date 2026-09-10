"""
Split -> fit XGBoost -> isotonic calibration -> evaluate -> save artifacts.

Split strategy (from MASTER BUILD):
  train: users[0:480],   t in {6,7,8}
  calib: users[480:640], t in {6,7,8}
  test:  users[640:800], t in {7,8,9}  <- unseen users AND later origins

Hyperparameters are FROZEN after this phase. Never tune again.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import joblib
from xgboost import XGBClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    precision_score,
)

from backend.app.services.features import FEATURE_NAMES
from ml.evaluate import compute_lead_times, compute_fp_rate_recovering

LABELED_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "labeled.parquet"
RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "users.parquet"
MODELS_DIR = Path(__file__).resolve().parent.parent / "backend" / "models"

TRAIN_ORIGINS = {6, 7, 8}
TEST_ORIGINS = {7, 8, 9}
SPLIT_SEED = 42


def _user_hash_split(user_ids, seed=SPLIT_SEED):
    """Hash-based split: 60% train, 20% calib, 20% test — preserves cohort balance."""
    rng = np.random.default_rng(seed)
    unique_ids = np.array(sorted(set(user_ids)))
    rng.shuffle(unique_ids)

    n = len(unique_ids)
    n_train = int(n * 0.60)
    n_calib = int(n * 0.20)

    train_ids = set(unique_ids[:n_train])
    calib_ids = set(unique_ids[n_train:n_train + n_calib])
    test_ids = set(unique_ids[n_train + n_calib:])

    return train_ids, calib_ids, test_ids


def split_data(df: pd.DataFrame):
    train_ids, calib_ids, test_ids = _user_hash_split(df["user_id"].unique())

    train_mask = df["user_id"].isin(train_ids) & df["as_of"].isin(TRAIN_ORIGINS)
    calib_mask = df["user_id"].isin(calib_ids) & df["as_of"].isin(TRAIN_ORIGINS)
    test_mask = df["user_id"].isin(test_ids) & df["as_of"].isin(TEST_ORIGINS)

    return df[train_mask], df[calib_mask], df[test_mask]


def verify_no_user_overlap(train_df, calib_df, test_df):
    train_users = set(train_df["user_id"].unique())
    calib_users = set(calib_df["user_id"].unique())
    test_users = set(test_df["user_id"].unique())

    assert train_users.isdisjoint(calib_users), "Train/calib user overlap!"
    assert train_users.isdisjoint(test_users), "Train/test user overlap!"
    assert calib_users.isdisjoint(test_users), "Calib/test user overlap!"
    print("No user overlap between splits.")


def train_model(X_train, y_train):
    model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        reg_lambda=2.0,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train, y_train)
    return model


def calibrate_model(model, X_calib, y_calib):
    raw_probs = model.predict_proba(X_calib)[:, 1]
    calibrator = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
    calibrator.fit(raw_probs, y_calib)
    return calibrator


def evaluate_model(model, calibrator, X_test, y_test, test_df, raw_df):
    raw_probs = model.predict_proba(X_test)[:, 1]
    y_prob = calibrator.predict(raw_probs)

    auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)
    brier = brier_score_loss(y_test, y_prob)

    top_decile_threshold = np.percentile(y_prob, 90)
    top_decile_mask = y_prob >= top_decile_threshold
    precision_top_decile = precision_score(
        y_test[top_decile_mask], (y_prob[top_decile_mask] >= 0.5).astype(int),
        zero_division=0,
    ) if top_decile_mask.sum() > 0 else 0.0
    precision_top_decile_actual = y_test[top_decile_mask].mean() if top_decile_mask.sum() > 0 else 0.0

    lead_times = compute_lead_times(model, calibrator, test_df, raw_df, FEATURE_NAMES)
    median_lead = float(np.median(lead_times)) if lead_times else 0.0

    fp_recovering = compute_fp_rate_recovering(model, calibrator, test_df, FEATURE_NAMES)

    metrics = {
        "roc_auc": round(auc, 4),
        "pr_auc": round(pr_auc, 4),
        "brier_score": round(brier, 4),
        "precision_at_top_decile": round(precision_top_decile_actual, 4),
        "median_lead_time_months": round(median_lead, 2),
        "lead_time_count": len(lead_times),
        "fp_rate_recovering": round(fp_recovering, 4),
        "test_size": len(y_test),
        "test_positive_rate": round(float(y_test.mean()), 4),
    }

    return metrics, y_prob


def main():
    print("Loading labeled data...")
    df = pd.read_parquet(LABELED_PATH)
    raw_df = pd.read_parquet(RAW_PATH)

    print(f"Total rows: {len(df)}")

    train_df, calib_df, test_df = split_data(df)
    print(f"Train: {len(train_df)} rows, Calib: {len(calib_df)} rows, Test: {len(test_df)} rows")
    print(f"Train positive rate: {train_df['y'].mean():.3f}")
    print(f"Test positive rate: {test_df['y'].mean():.3f}")

    verify_no_user_overlap(train_df, calib_df, test_df)

    X_train = train_df[FEATURE_NAMES].values
    y_train = train_df["y"].values
    X_calib = calib_df[FEATURE_NAMES].values
    y_calib = calib_df["y"].values
    X_test = test_df[FEATURE_NAMES].values
    y_test = test_df["y"].values

    print("\nTraining XGBoost...")
    model = train_model(X_train, y_train)

    print("Calibrating with isotonic regression...")
    calibrator = calibrate_model(model, X_calib, y_calib)

    print("Evaluating on test set...")
    metrics, y_prob = evaluate_model(model, calibrator, X_test, y_test, test_df, raw_df)

    print(f"\n{'='*50}")
    print("METRICS:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    print(f"{'='*50}")

    auc = metrics["roc_auc"]
    if auc > 0.92:
        print(f"\nWARNING: AUC {auc} > 0.92 -- data may be too easy, consider regenerating")
    elif auc < 0.78:
        print(f"\nWARNING: AUC {auc} < 0.78 -- model underfitting")
    else:
        print(f"\nAUC {auc} in target range [0.78, 0.90]")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, MODELS_DIR / "xgb_spiral.joblib")
    joblib.dump(calibrator, MODELS_DIR / "calibrator.joblib")

    with open(MODELS_DIR / "feature_names.json", "w") as f:
        json.dump(FEATURE_NAMES, f, indent=2)

    with open(MODELS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nArtifacts saved to {MODELS_DIR}/")
    print("  xgb_spiral.joblib")
    print("  calibrator.joblib")
    print("  feature_names.json")
    print("  metrics.json")


if __name__ == "__main__":
    main()
