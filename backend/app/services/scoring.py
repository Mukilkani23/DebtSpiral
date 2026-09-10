"""
Model loading, prediction, and calibration.
Score = round(100 * calibrated_probability).
"""

import joblib
import numpy as np
from pathlib import Path
from ..services.features import FEATURE_NAMES


_model = None
_calibrator = None
_model_trained_at: str | None = None


def load_model(model_path: str, calibrator_path: str | None = None) -> None:
    global _model, _calibrator, _model_trained_at
    mp = Path(model_path)
    if not mp.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    _model = joblib.load(mp)

    cp = Path(calibrator_path) if calibrator_path else mp.parent / "calibrator.joblib"
    if cp.exists():
        _calibrator = joblib.load(cp)

    import os, time
    _model_trained_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(mp)))


def is_loaded() -> bool:
    return _model is not None


def get_trained_at() -> str | None:
    return _model_trained_at


def predict(features: dict[str, float]) -> tuple[float, int]:
    """Returns (calibrated_probability, risk_score_0_100)."""
    if _model is None:
        raise RuntimeError("Model not loaded")
    X = np.array([[features[f] for f in FEATURE_NAMES]])
    raw_prob = _model.predict_proba(X)[:, 1]
    if _calibrator is not None:
        prob = float(_calibrator.predict(raw_prob)[0])
    else:
        prob = float(raw_prob[0])
    prob = max(0.0, min(1.0, prob))
    score = round(100 * prob)
    return prob, score


def get_booster():
    """Return the raw model for SHAP (TreeExplainer needs the booster)."""
    return _model
