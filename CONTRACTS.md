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

---

## v5 Extension — Demo Account, Tier Config, Extra-Funds Allocation

> Added after the v4 freeze. Existing sections above are unchanged.
> This section documents new, additive endpoints only.

### DemoAccountResponse

```json
{
  "persona_id": "C",
  "balance_inr": 10400.0,
  "allocated": { "tier_1": 3250.0, "tier_2": 1500.0, "tier_3": 250.0 },
  "last_allocation": {
    "extra_amount": 5000.0,
    "allocation": [
      { "tier": 1, "amount": 3250.0, "reason": "..." },
      { "tier": 2, "amount": 1500.0, "reason": "..." },
      { "tier": 3, "amount": 250.0, "reason": "..." }
    ],
    "priority_order": [1, 2, 3],
    "suggestion": "..."
  }
}
```

`balance_inr` is server-authoritative. Initial balance is derived from the
persona's last month (`income - essential_spend - discretionary_spend - repayment`,
floored at 0) — not invented. `last_allocation` is `null` until a positive
adjustment has been made.

### GET /admin/account?persona_id={id}

Returns the demo account for the given persona. 404 if the persona is unknown.

> Deviation from the original feature request text: the request named this
> `GET /admin/account` with no id, implying a server-side "currently selected
> persona." No such concept exists anywhere else in this codebase (personas
> are stateless, addressed by id everywhere else — `GET /personas/{id}`,
> `POST /score`, `POST /transaction`, etc.). Introducing global "current
> user" state would be a new abstraction not used anywhere else in the
> project. `persona_id` is a required query param instead, consistent with
> the rest of the API.

### POST /admin/account/adjust

Request:
```json
{ "persona_id": "C", "amount": 5000, "reason": "demo_credit" }
```

`amount` may be negative (demo debit). A negative `amount` that would drop
`balance_inr` below 0 returns `400`. Unknown `persona_id` returns `404`.

Response: `DemoAccountResponse`.

If `amount > 0`, the backend also:
1. Computes the current risk assessment for the persona (existing `/score` logic).
2. Runs the allocation engine (`extra_funds_ratios` from tier config, conservative
   shift applied if `spiral_detected` or `band` is `ELEVATED`/`HIGH`).
3. Records the result as `last_allocation` and adds it to `allocated`.
4. Fires a non-blocking notification via the existing NotificationAdapter
   (`services/notify.py` — same Twilio/fallback path as transaction nudges).
   Delivery failure never fails the HTTP response.

If `amount <= 0`, no allocation is computed and `last_allocation` is left
unchanged from its prior value.

> Deviation: this endpoint does NOT push the credit through the simulator to
> mutate persona history / re-score the risk model. The simulator's
> `step_month` has no concept of a windfall deposit distinct from spending —
> forcing one through would mean inventing simulator semantics not used
> anywhere else. The account ledger is intentionally a separate "demo wallet"
> from the risk-model input data (`persona.history`). The response includes
> the account's current allocation, computed against the persona's *existing*
> risk assessment — it does not claim the credit itself changed the risk
> score. Deeper simulator integration is a follow-up, not done in this pass.

### TierConfigResponse

```json
{
  "category_tiers": {
    "food_delivery": 3, "shopping": 3, "entertainment": 3,
    "travel": 2, "electronics": 2, "subscription": 2, "other": 2
  },
  "extra_funds_ratios": { "1": 0.6, "2": 0.3, "3": 0.1 }
}
```

### GET /config/tiers

Returns the current tier configuration.

### POST /config/tiers

Request (either or both fields, partial update):
```json
{
  "category_tiers": { "shopping": 2 },
  "extra_funds_ratios": { "1": 0.5, "2": 0.3, "3": 0.2 }
}
```

Validation: each tier must be `1|2|3` (400 otherwise); `extra_funds_ratios`
values must sum to `1.0 ± 0.01` (400 otherwise). Response: `TierConfigResponse`.

Changing `category_tiers` immediately affects the next `/transaction` call's
tier lookup (the rule engine's `TIER_2` reason code and severity gating).
Changing `extra_funds_ratios` immediately affects the next
`/admin/account/adjust` allocation.

> Deviation: unlike the literal spec text ("Persist to tier_config.json"),
> `POST /config/tiers` mutates an **in-memory** working copy only — it does
> not rewrite the seed JSON file on disk. This matches the existing
> `session_store.py` pattern: `personas.json` is read once as seed data and
> is never rewritten by runtime mutations; `POST /reset` restores from an
> in-memory baseline, not by re-reading the file. Rewriting the checked-in
> seed file on every demo session would dirty the repository on every test
> run and every demo click. `tier_config_store.py` follows the same
> load-once / in-memory-mutate / reset-from-baseline pattern.

### POST /reset (extended)

In addition to the existing behavior (restore personas, clear notification
dedup), `/reset` now also restores all demo account balances to their
initial (persona-derived) values and restores tier config to its seed
defaults. No new reset endpoint was added — this reuses the existing one,
per project rules against redundant reset systems.

### Notification: EXTRA_FUNDS_ALLOCATION_SUGGESTION

Fired as a non-blocking `BackgroundTask` via the existing
`services/notify.send()` — the same adapter and Twilio/fallback path used
by transaction nudges. No second notification system was introduced. The
message explicitly states it is a recommendation, not a completed payment.

---

## v5.1 Extension — Transaction Balance Protection (INSUFFICIENT_BALANCE)

> Added after the v5 account/tier-config extension. Existing sections
> above (including `TransactionResponse`) are unchanged for a *successful*
> transaction.

**Invariant:** `POST /transaction` requires `amount_inr <= available_balance`
(the persona's `services/account_store.py` demo ledger, not persona.history)
before any other work happens. The check and the balance deduction are one
atomic call (`account_store.adjust_balance(persona_id, -amount_inr)`) — there
is no read-then-write gap, so two rapid sequential requests can't both pass
against a stale balance.

### InsufficientBalanceResponse

On rejection, `POST /transaction` returns **HTTP 400** (matching the existing
`/admin/account/adjust` convention for balance-validation failures) with a
flat body — no `{"detail": ...}` wrapper:

```json
{
  "success": false,
  "error_code": "INSUFFICIENT_BALANCE",
  "message": "Insufficient balance",
  "requested_amount_inr": 25000,
  "available_balance_inr": 20000,
  "shortfall_inr": 5000
}
```

On rejection:
- The account balance is **not** mutated.
- `persona.history` is **not** mutated (feature engine, XGBoost, loop
  detector, and rule engine never run).
- No nudge is created and no notification fires.
- The response carries **no** `reason_codes` and **no** `nudge` field —
  this codebase has no `UNPLANNED_EXPENSE` code (confirmed by audit: the 8
  codes in `rules.py` don't include it), so nothing analogous fires either.

`amount_inr <= 0` is already rejected by the existing `TransactionRequest`
schema (`Field(gt=0, le=500000)`) as **HTTP 422** — no new validation was
needed for that case.

This check is independent of `risk_score`, `spiral_detected`, and tier: a
healthy, non-spiraling persona is rejected exactly the same way a spiraling
one is, purely on the balance math.

### Notification customization (nudge text only)

The WhatsApp/notification text for a **successfully flagged** transaction
now appends the model's top SHAP driver, e.g. *"...Biggest driver:
Discretionary spending ratio."* This is composed in `api/transaction.py`
from the existing `ShapExplanation` — `rules.py` is untouched and still
never imports `explain.py` or sees a SHAP value; `reason_codes` are
unaffected. This customization does not apply to the `INSUFFICIENT_BALANCE`
path (there is no nudge on that path at all).

---

## Module Boundaries

- `api/*` may only import `services/*` and `schemas`
- `services/*` may NOT import `api/*`
- `features.py`, `loop_detector.py`, `rules.py`, `simulator.py` are PURE: no I/O, no globals, no config reads
- Request schemas use `extra="forbid"` — unknown fields are rejected
- No `/notify` endpoint exists. Notification is a server-side side effect only.
- CORS: allow-list `http://localhost:5173` only
