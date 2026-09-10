"""
Forward-window labeling: y=1 if loop_detector fires in [t+1, t+3].
Anti-leakage: features from t-6..t, labels from t+1..t+3 (disjoint windows).
Merges labels onto feature table → data/processed/labeled.parquet
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from backend.app.services.loop_detector import evaluate

FEATURES_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "features.parquet"
RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "users.parquet"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "labeled.parquet"

LABEL_WINDOW = 3  # look ahead t+1..t+3


def compute_labels(raw_df: pd.DataFrame, feat_df: pd.DataFrame) -> pd.DataFrame:
    labels = []

    for _, row in feat_df.iterrows():
        uid = row["user_id"]
        as_of = row["as_of"]

        user_history = raw_df[raw_df["user_id"] == uid].to_dict("records")

        y = 0
        for future_t in range(as_of + 1, as_of + LABEL_WINDOW + 1):
            if evaluate(user_history, at_month=future_t):
                y = 1
                break

        labels.append({
            "user_id": uid,
            "as_of": as_of,
            "y": y,
        })

    label_df = pd.DataFrame(labels)
    return feat_df.merge(label_df, on=["user_id", "as_of"], how="left")


def main():
    print("Loading feature table and raw data...")
    feat_df = pd.read_parquet(FEATURES_PATH)
    raw_df = pd.read_parquet(RAW_PATH)

    print(f"Feature rows: {len(feat_df)}")
    print(f"Computing forward-window labels (window={LABEL_WINDOW})...")

    labeled_df = compute_labels(raw_df, feat_df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    labeled_df.to_parquet(OUTPUT_PATH, index=False)

    print(f"Saved to {OUTPUT_PATH}")
    print(f"Shape: {labeled_df.shape}")

    pos = labeled_df["y"].sum()
    total = len(labeled_df)
    rate = pos / total * 100
    print(f"\nLabel distribution:")
    print(f"  Positive (y=1): {pos} ({rate:.1f}%)")
    print(f"  Negative (y=0): {total - pos} ({100 - rate:.1f}%)")
    print(f"  Target range: 20-35%")

    if rate < 20 or rate > 35:
        print(f"  WARNING: Label rate {rate:.1f}% outside target 20-35% -- may need tuning")

    print(f"\nLabels by cohort:")
    by_cohort = labeled_df.groupby("cohort")["y"].agg(["sum", "count", "mean"])
    by_cohort.columns = ["positive", "total", "rate"]
    by_cohort["rate"] = (by_cohort["rate"] * 100).round(1)
    print(by_cohort.to_string())


if __name__ == "__main__":
    main()
