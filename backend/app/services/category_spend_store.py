"""
Per-persona, per-category spend tracker (since last /reset). Used only to
build person-specific notification context (budget usage, new-category
detection, amount-anomaly detection) — never used for risk scoring or
transaction authorization, which come from persona.history / account_store.

Not on the PURE list — mutable in-memory state, mirrors session_store.py.
"""

_spend: dict[str, dict[str, float]] = {}
_amounts: dict[str, dict[str, list[float]]] = {}


def get_spend(persona_id: str, category: str) -> float:
    return _spend.get(persona_id, {}).get(category, 0.0)


def get_amount_history(persona_id: str, category: str) -> list[float]:
    return list(_amounts.get(persona_id, {}).get(category, []))


def is_new_category(persona_id: str, category: str) -> bool:
    return category not in _spend.get(persona_id, {})


def record(persona_id: str, category: str, amount: float) -> None:
    persona_spend = _spend.setdefault(persona_id, {})
    persona_spend[category] = persona_spend.get(category, 0.0) + amount

    persona_amounts = _amounts.setdefault(persona_id, {})
    persona_amounts.setdefault(category, []).append(amount)


def reset_all() -> None:
    _spend.clear()
    _amounts.clear()
