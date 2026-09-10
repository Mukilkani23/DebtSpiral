"""
SHAP TreeExplainer wrapper. Model-level attribution only.
SHAP runs on the uncalibrated booster (additive in margin space).
Returns top 6 features by |shap|.
"""

import numpy as np
import shap
from ..services.features import FEATURE_NAMES

DISPLAY_NAMES = {
    "utilization_level": "Credit utilization level",
    "utilization_trend": "Credit utilization climbing",
    "dti_level": "Debt-to-income ratio",
    "dti_trend": "Debt-to-income growing",
    "min_payment_ratio": "Repayment discipline eroding",
    "min_payment_ratio_trend": "Repayment trend declining",
    "stc_frequency": "Short-term borrowing increasing",
    "stc_amount_ratio": "Short-term credit amount ratio",
    "discretionary_ratio": "Discretionary spending ratio",
    "income_volatility": "Income instability",
    "spending_volatility": "Spending instability",
    "repayment_trend": "Repayment trend",
    "delta_30d_debt": "30-day debt acceleration",
    "delta_90d_debt": "90-day debt acceleration",
    "recovery_slope": "Recovery capacity shrinking",
    "absolute_debt_inr": "Outstanding debt level",
}

_explainer = None


def _get_explainer(model):
    global _explainer
    if _explainer is None:
        _explainer = shap.TreeExplainer(model)
    return _explainer


def explain(features: dict[str, float], model) -> dict:
    """
    Returns ShapExplanation-shaped dict: {base_value, items: [{feature, display_name, value, shap, direction}]}
    Top 6 by |shap|, sorted descending.
    """
    explainer = _get_explainer(model)
    X = np.array([[features[f] for f in FEATURE_NAMES]])
    shap_values = explainer.shap_values(X)

    if isinstance(shap_values, list):
        sv = shap_values[1][0]
    elif shap_values.ndim == 2:
        sv = shap_values[0]
    else:
        sv = shap_values[0]

    base = float(explainer.expected_value if np.isscalar(explainer.expected_value)
                 else explainer.expected_value[1] if len(explainer.expected_value) > 1
                 else explainer.expected_value[0])

    items = []
    for i, fname in enumerate(FEATURE_NAMES):
        items.append({
            "feature": fname,
            "display_name": DISPLAY_NAMES.get(fname, fname),
            "value": round(float(features[fname]), 4),
            "shap": round(float(sv[i]), 4),
            "direction": "+" if sv[i] > 0 else "-",
        })

    items.sort(key=lambda x: abs(x["shap"]), reverse=True)
    return {"base_value": round(base, 4), "items": items[:6]}
