# DebtSpiral API Contract — FROZEN

> This file is frozen after Phase 0. Nobody — human or agent — edits it.
> If a task seems to require changing this file, STOP and ask.

## Base URL

`http://localhost:8000`

---

## Data Models

### MonthlySnapshot

| Field                        | Type  | Example  |
|------------------------------|-------|----------|
| `month_index`                | int   | `9`      |
| `income_inr`                 | float | `50000`  |
| `essential_spend_inr`        | float | `22000`  |
| `discretionary_spend_inr`    | float | `14500`  |
| `outstanding_debt_inr`       | float | `78000`  |
| `credit_limit_inr`           | float | `120000` |
| `repayment_inr`              | float | `3100`   |
| `min_due_inr`                | float | `3000`   |
| `short_term_credit_count`    | int   | `2`      |
| `short_term_credit_amount_inr` | float | `9000` |
| `emi_obligations_inr`        | float | `6000`   |

### Persona

| Field               | Type                    | Required |
|----------------------|-------------------------|----------|
| `persona_id`         | str enum `A\|B\|C\|D\|E` | yes      |
| `label`              | str                     | yes      |
| `monthly_income_inr` | int                     | yes      |
| `income_type`        | enum `stable\|variable` | yes      |
| `credit_limit_inr`   | int                     | yes      |
| `is_live`            | bool                    | yes      |
| `history`            | list[MonthlySnapshot]   | yes      |
| `narrative`          | str                     | yes      |

### RiskAssessment

```json
{
  "risk_score": 87,
  "probability": 0.87,
  "band": "HIGH",
  "spiral_detected": true,
  "spiral_confirmed_month": 8,
  "model_warned_month": 5,
  "lead_time_months": 3.0
}
```

Bands: `LOW` (0-29) | `MODERATE` (30-49) | `ELEVATED` (50-69) | `HIGH` (70-100)

### ShapExplanation

```json
{
  "base_value": 0.25,
  "items": [
    {
      "feature": "utilization_trend",
      "display_name": "Credit utilization climbing",
      "value": 0.062,
      "shap": 0.14,
      "direction": "+"
    }
  ]
}
```

Top 6 items by |shap|, sorted descending.

### ReasonCode

```json
{
  "code": "HIGH_UTILIZATION",
  "label": "Credit already stretched",
  "detail": "utilization 68% — above the 60% threshold",
  "severity": 3
}
```

Max 4 returned per transaction, sorted by severity descending.

Valid codes: `TIER_2` | `LARGE_RELATIVE_TXN` | `BUDGET_EXCEEDED` | `HIGH_UTILIZATION` | `RECENT_SHORT_TERM_CREDIT` | `LOW_RECOVERY_CAPACITY` | `SPIRAL_TRAJECTORY` | `ELEVATED_RISK_BAND`

### NudgeEvent

```json
{
  "nudge_id": "uuid-string",
  "persona_id": "C",
  "transaction": { "category": "food_delivery", "amount_inr": 2000 },
  "reason_codes": [],
  "risk_before": 87,
  "risk_after": 91,
  "suggested_alternative": "Home-cooked meal, ~₹250 — ₹1,750 saved",
  "created_at": "2026-09-10T12:00:00Z",
  "delivery": {
    "channel": "twilio",
    "status": "pending",
    "error": null
  }
}
```

### ProjectionResult

```json
{
  "horizon_months": [3, 6, 12],
  "scenario_a": {
    "debt": [80000, 95000, 142000],
    "risk": [88, 90, 94],
    "savings": [0, 0, 0]
  },
  "scenario_b": {
    "debt": [75000, 82000, 110000],
    "risk": [82, 75, 60],
    "savings": [2000, 8000, 22000]
  },
  "difference_inr": { "3": 5000, "6": 13000, "12": 32000 },
  "cost_of_next_decision": {
    "lever": "discretionary_reduction",
    "delta_per_month_inr": 5000,
    "debt_avoided_12mo_inr": 31400
  }
}
```

---

## Endpoints

### GET /personas

Response: `Persona[]` (without `history`), each augmented with:
- `current_risk_score: int`
- `spiral_detected: bool`

### GET /personas/{id}

Response: full `Persona` with `history` + `RiskAssessment` + `ShapExplanation` + `model_warned_month` + `spiral_confirmed_month`.

404 on unknown id.

### POST /score

Request:
```json
{ "persona_id": "C", "as_of_month": 12 }
```
`as_of_month` is optional (defaults to latest).

Response:
```json
{
  "risk_score": 87,
  "probability": 0.87,
  "band": "HIGH",
  "spiral_detected": true,
  "spiral_confirmed_month": 8,
  "model_warned_month": 5,
  "lead_time_months": 3.0,
  "features_summary": {},
  "shap": {}
}
```

### POST /transaction

Request:
```json
{ "persona_id": "C", "category": "food_delivery", "amount_inr": 2000 }
```

Validation:
- persona must exist and `is_live == true` (403 otherwise)
- `0 < amount_inr <= 500000`
- `category` in enum: `food_delivery | shopping | entertainment | travel | electronics | subscription | other`

Response (sync, <400ms):
```json
{
  "flagged": true,
  "risk_score": 91,
  "risk_before": 87,
  "probability": 0.91,
  "band": "HIGH",
  "spiral_detected": true,
  "reason_codes": [],
  "shap": {},
  "nudge": {
    "nudge_id": "uuid",
    "message": "...",
    "suggested_alternative": "...",
    "delivery": { "channel": "fallback", "status": "pending", "error": null }
  },
  "nudge_triggered": true
}
```

Async side effect: BackgroundTask sends notification via Twilio or fallback.

### POST /project

Request:
```json
{
  "persona_id": "C",
  "direction": "risk",
  "levers": {
    "discretionary_reduction_inr": 5000,
    "repayment_increase_inr": 2000,
    "stc_reduction_count": 1
  }
}
```

Response: `ProjectionResult`

### POST /reset

No body. Restores all personas from `personas.json`. Returns `{ "status": "ok" }`.

### GET /health

Response:
```json
{
  "status": "ok",
  "model_loaded": true,
  "model_trained_at": "2026-09-10T...",
  "personas_loaded": 5,
  "twilio_configured": false,
  "uptime_s": 42.5
}
```

---

## Module Boundaries

- `api/*` may only import `services/*` and `schemas`
- `services/*` may NOT import `api/*`
- `features.py`, `loop_detector.py`, `rules.py`, `simulator.py` are PURE: no I/O, no globals, no config reads
- Request schemas use `extra="forbid"` — unknown fields are rejected
- No `/notify` endpoint exists. Notification is a server-side side effect only.
- CORS: allow-list `http://localhost:5173` only
