"""
Build feature table from raw user data.
For each user, compute features at prediction origins t=6..9 (need 6 months history).
Output: data/processed/features.parquet
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from backend.app.services.features import build, FEATURE_NAMES

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "users.parquet"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "features.parquet"

PREDICTION_ORIGINS = list(range(6, 10))  # months 6, 7, 8, 9


def build_feature_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    user_ids = df["user_id"].unique()

    for uid in user_ids:
        user_df = df[df["user_id"] == uid].sort_values("month_index")
        cohort = user_df["cohort"].iloc[0]

        history = user_df.to_dict("records")

        for t in PREDICTION_ORIGINS:
            history_up_to_t = [s for s in history if s["month_index"] <= t]
            if len(history_up_to_t) < 4:
                continue

            feats = build(history_up_to_t, as_of=t)
            feats["user_id"] = uid
            feats["cohort"] = cohort
            feats["as_of"] = t
            rows.append(feats)

    feat_df = pd.DataFrame(rows)
    col_order = ["user_id", "cohort", "as_of"] + FEATURE_NAMES
    return feat_df[col_order]


def main():
    print(f"Reading raw data from {RAW_PATH}...")
    df = pd.read_parquet(RAW_PATH)
    print(f"Raw shape: {df.shape}")

    print(f"Building features at prediction origins {PREDICTION_ORIGINS}...")
    feat_df = build_feature_table(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    feat_df.to_parquet(OUTPUT_PATH, index=False)

    print(f"Saved to {OUTPUT_PATH}")
    print(f"Feature table shape: {feat_df.shape}")
    print(f"Users: {feat_df['user_id'].nunique()}")
    print(f"Prediction origins: {sorted(feat_df['as_of'].unique())}")
    print(f"\nAny NaN: {feat_df[FEATURE_NAMES].isna().any().any()}")
    print(f"\nFeature stats:")
    print(feat_df[FEATURE_NAMES].describe().round(4).to_string())


if __name__ == "__main__":
    main()
