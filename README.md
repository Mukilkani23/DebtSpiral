# DebtSpiral — Early Detection of Debt Spirals

An early-warning system that distinguishes temporary financial setbacks from emerging debt spirals, using trajectory analysis rather than static thresholds.

**100% synthetic data. No PII, no account numbers, no merchant strings, no real financial data.**

## Architecture

```
Raw txns → [Aggregation boundary] → Features (ratios & trends only)
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
              XGBoost Model      Loop Detector        Rule Engine
              (forward-looking)  (present-tense)      (event-level)
              P(spiral in        "IS spiraling"       "WHY this txn
               t+1..t+3)         deterministic         was flagged"
                    │                   │                   │
                    └───────────────────┴───────────────────┘
                                        ▼
                              Risk Assessment + Nudge
```

**Privacy by construction:** every feature is a ratio or a trend. The model never needs to know where you shopped, only that the category was discretionary. No identifiable information crosses the aggregation boundary.

**Autonomy:** we inform, we never block.

## Quick Start

```bash
make install        # install Python + Node dependencies
make api            # start FastAPI backend on :8000
make web            # start Vite frontend on :5173 (separate terminal)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Pydantic v2 + uvicorn |
| ML | XGBoost + sklearn CalibratedClassifierCV |
| Explainability | SHAP TreeExplainer |
| Frontend | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Notifications | Twilio WhatsApp Sandbox (optional) |

## Key Metrics

_Generated after ML training (Phase 3)_

| Metric | Target |
|--------|--------|
| Median lead time | ≥ 2.0 months |
| ROC-AUC | 0.78 – 0.90 |
| PR-AUC | ≥ 0.55 |
| Brier score | ≤ 0.16 |
| FP rate (recovering users) | ≤ 0.15 |
