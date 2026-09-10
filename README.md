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

### Prerequisites

- Python 3.11+
- Node.js 18+

### 1. Install Python dependencies

```bash
pip install fastapi uvicorn pydantic-settings xgboost scikit-learn shap joblib numpy
```

### 2. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 3. Start the backend (Terminal 1)

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

The API loads the trained XGBoost model and 5 demo personas at startup.

### 4. Start the frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

### 5. Open in browser

Go to **http://localhost:5173**

### Optional: Twilio WhatsApp notifications

Create a `.env` file in the project root:

```env
TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
DEMO_WHATSAPP_TO=whatsapp:+91XXXXXXXXXX
```

### Optional: Re-run the ML pipeline from scratch

```bash
python -m backend.ml.generate_dataset    # generate 800 synthetic users
python -m backend.ml.build_features      # compute 16 features per origin
python -m backend.ml.label               # forward-window labeling
python -m backend.ml.train               # XGBoost + isotonic calibration
python -m backend.ml.evaluate            # lead time + FP analysis
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Model status, persona count, uptime |
| GET | `/personas` | List all personas with risk scores |
| GET | `/personas/{id}` | Persona detail + SHAP explanation |
| POST | `/score` | Compute risk score for a persona |
| POST | `/transaction` | Process transaction, flag if risky, generate nudge |
| POST | `/project` | Project debt scenarios (do nothing vs change behavior) |
| POST | `/reset` | Reset all personas to initial state |

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

## Model Metrics (Trained)

| Metric | Value |
|--------|-------|
| ROC-AUC | 0.8267 |
| PR-AUC | 0.6097 |
| Brier score | 0.1401 |
| Median lead time | 2.0 months |
| FP rate (recovering users) | 0.0462 |
| Precision @ top decile | 0.7308 |
