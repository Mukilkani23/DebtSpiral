"""
Server-side demo account ledger. One account per persona_id.
The server is authoritative — the frontend only sends adjustment actions.

Initial balance is derived from the persona's own last-month state
(income - essentials - discretionary - repayment, floored at 0), not invented.
Not on the PURE list — this module holds mutable in-memory state by design,
mirroring session_store.py's pattern.
"""

from ..schemas import Persona

_balances: dict[str, float] = {}
_allocated: dict[str, dict[str, float]] = {}
_last_allocation: dict[str, dict | None] = {}
_baseline_balances: dict[str, float] = {}


def _initial_balance(persona: Persona) -> float:
    if not persona.history:
        return 0.0
    last = persona.history[-1]
    available = (
        last.income_inr - last.essential_spend_inr
        - last.discretionary_spend_inr - last.repayment_inr
    )
    return round(max(available, 0.0), 2)


def init_accounts(personas: list[Persona]) -> None:
    _balances.clear()
    _allocated.clear()
    _last_allocation.clear()
    _baseline_balances.clear()
    for p in personas:
        bal = _initial_balance(p)
        _balances[p.persona_id] = bal
        _baseline_balances[p.persona_id] = bal
        _allocated[p.persona_id] = {"tier_1": 0.0, "tier_2": 0.0, "tier_3": 0.0}
        _last_allocation[p.persona_id] = None


def get_account(persona_id: str) -> dict | None:
    if persona_id not in _balances:
        return None
    return {
        "persona_id": persona_id,
        "balance_inr": _balances[persona_id],
        "allocated": dict(_allocated[persona_id]),
        "last_allocation": _last_allocation[persona_id],
    }


def adjust_balance(persona_id: str, amount: float) -> dict:
    if persona_id not in _balances:
        raise KeyError(persona_id)
    new_balance = round(_balances[persona_id] + amount, 2)
    if new_balance < 0:
        raise ValueError("Adjustment would result in a negative balance")
    _balances[persona_id] = new_balance
    return get_account(persona_id)


def record_allocation(persona_id: str, allocation_result: dict) -> None:
    _last_allocation[persona_id] = allocation_result
    for item in allocation_result["allocation"]:
        key = f"tier_{item['tier']}"
        _allocated[persona_id][key] = round(
            _allocated[persona_id].get(key, 0.0) + item["amount"], 2
        )


def reset_all() -> None:
    for pid, bal in _baseline_balances.items():
        _balances[pid] = bal
        _allocated[pid] = {"tier_1": 0.0, "tier_2": 0.0, "tier_3": 0.0}
        _last_allocation[pid] = None
