# DebtSpiral — Early Detection of Debt Spirals

An early-warning system that distinguishes temporary financial setbacks from
emerging debt spirals, using trajectory analysis rather than static
thresholds.

**100% synthetic data. No PII, no account numbers, no merchant strings, no
real financial data.**

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

**Privacy by construction:** every feature is a ratio or a trend. The model
never needs to know where you shopped, only that the category was
discretionary. No identifiable information crosses the aggregation boundary.

**Autonomy:** we inform, we never block.

## Project Structure

```
DebtSpiral/
├── backend/
│   ├── app/            # FastAPI application (api, services, schemas, config)
│   ├── models/         # Trained XGBoost model artifacts
│   └── tests/          # pytest suite
├── ml/                 # Dataset generation, feature/label pipeline, training
├── frontend/           # React + TypeScript + Vite app
├── data/               # Generated datasets (gitignored: raw/ and processed/)
├── scripts/            # Utility scripts
├── CONTRACTS.md         # API request/response schemas
└── .env                # Local secrets (gitignored — see Setup below)
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+

### 1. Install Python dependencies

```bash
pip install -r backend/requirements.txt
```

### 2. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 3. Configure environment

Copy the example file and fill in values as needed:

```bash
cp .env.example .env
```

The app runs fine with the defaults — Twilio notifications are disabled
out of the box. See [Twilio WhatsApp notifications](#optional-twilio-whatsapp-notifications)
to enable them.

### 4. Start the backend (Terminal 1)

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

The API loads the trained XGBoost model and 5 demo personas at startup.

### 5. Start the frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

### 6. Open in browser

Go to **http://localhost:5173**

### Optional: Twilio WhatsApp notifications

Set the following in your `.env` file (see `.env.example` for the full list):

```env
TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
DEMO_WHATSAPP_TO=whatsapp:+91XXXXXXXXXX
```

You can authenticate with either the Account Auth Token **or** a Twilio API
Key (recommended — scoped and revocable independently of the account-level
token):

```env
TWILIO_API_KEY_SID=SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_API_KEY_SECRET=your_api_key_secret
```

If both an API Key and an Auth Token are set, the API Key takes priority.

> **Never commit `.env`.** It is already listed in `.gitignore`. If you ever
> paste credentials into a chat, ticket, or doc, treat them as compromised
> and rotate them in the [Twilio Console](https://console.twilio.com).

### Optional: Re-run the ML pipeline from scratch

```bash
python -m backend.ml.generate_dataset    # generate 800 synthetic users
python -m backend.ml.build_features      # compute 16 features per origin
python -m backend.ml.label               # forward-window labeling
python -m backend.ml.train               # XGBoost + isotonic calibration
python -m backend.ml.evaluate            # lead time + FP analysis
```

### Run backend tests

```bash
python -m pytest backend/tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Model status, persona count, uptime |
| GET | `/personas` | List all personas with risk scores |
| GET | `/personas/{id}` | Persona detail + SHAP explanation |
| POST | `/score` | Compute risk score for a persona |
| POST | `/transaction` | Process transaction, flag if risky, generate nudge |
| POST | `/project` | Project debt scenarios (do nothing vs change behavior) |
| POST | `/reset` | Reset all personas, demo accounts, and tier config to initial state |
| GET | `/admin/account?persona_id={id}` | Demo account balance + last allocation for a persona |
| POST | `/admin/account/adjust` | Add/reduce demo balance; positive amounts trigger tier-aware allocation + notification |
| GET | `/config/tiers` | Current category-tier map + extra-funds allocation ratios |
| POST | `/config/tiers` | Update category tiers and/or allocation ratios (in-memory, restored on reset) |

See [CONTRACTS.md](CONTRACTS.md) for full request/response schemas and the
"v5 Extension" section for the demo account/tier-config design notes.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Pydantic v2 + uvicorn |
| ML | XGBoost + sklearn CalibratedClassifierCV |
| Explainability | SHAP TreeExplainer |
| Frontend | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Notifications | Twilio WhatsApp (sandbox or approved sender) |

### Transaction Balance Protection

DebtSpiral treats account balance as a server-authoritative constraint on
its **Demo Account Ledger** (not a real bank integration). A transaction is
accepted only when:

```
transaction_amount <= available_balance
```

If the requested amount exceeds the available balance, `POST /transaction`
rejects it with `INSUFFICIENT_BALANCE` (HTTP 400) and does not mutate the
account balance, persona history, or trigger any risk scoring, rule
evaluation, or notification — see [CONTRACTS.md](CONTRACTS.md) for the
exact response shape.

### Context-aware notifications

DebtSpiral generates notification content from the user's actual tier
configuration, category budget, and category spend history — not one
hardcoded message. The same ₹500-over-budget alert reads differently for
a ₹3,000 Food Delivery allocation than for a ₹30,000 Shopping allocation,
because the numbers come from `GET /config/tiers` and each persona's own
spend, not a template string. Changing a category's budget via `POST
/config/tiers` changes the very next notification for that category. See
[CONTRACTS.md](CONTRACTS.md)'s "Person-Specific Notification Messages"
section for the full event-type list and priority order.

## Model Metrics (Trained)

| Metric | Value |
|--------|-------|
| ROC-AUC | 0.8267 |
| PR-AUC | 0.6097 |
| Brier score | 0.1401 |
| Median lead time | 2.0 months |
| FP rate (recovering users) | 0.0462 |
| Precision @ top decile | 0.7308 |
