"""
Transaction affordability: transaction_amount <= available_balance.
Balance-relative (not hardcoded to a specific amount) so the rule is proven
to work for ANY balance / ANY positive amount, not just one demo number.
"""


def _set_balance(client, persona_id, target):
    current = client.get("/admin/account", params={"persona_id": persona_id}).json()["balance_inr"]
    delta = round(target - current, 2)
    if delta != 0:
        resp = client.post("/admin/account/adjust", json={
            "persona_id": persona_id, "amount": delta, "reason": "test_setup",
        })
        assert resp.status_code == 200
    return target


def test_insufficient_balance_rejected_with_exact_shortfall(client):
    _set_balance(client, "C", 20000)
    resp = client.post("/transaction", json={
        "persona_id": "C", "category": "shopping", "amount_inr": 25000,
    })
    assert resp.status_code == 400
    data = resp.json()
    assert data["success"] is False
    assert data["error_code"] == "INSUFFICIENT_BALANCE"
    assert data["requested_amount_inr"] == 25000
    assert data["available_balance_inr"] == 20000
    assert data["shortfall_inr"] == 5000

    account = client.get("/admin/account", params={"persona_id": "C"}).json()
    assert account["balance_inr"] == 20000


def test_exact_balance_transaction_succeeds(client):
    _set_balance(client, "C", 20000)
    resp = client.post("/transaction", json={
        "persona_id": "C", "category": "shopping", "amount_inr": 20000,
    })
    assert resp.status_code == 200
    account = client.get("/admin/account", params={"persona_id": "C"}).json()
    assert account["balance_inr"] == 0


def test_below_balance_transaction_succeeds(client):
    _set_balance(client, "C", 20000)
    resp = client.post("/transaction", json={
        "persona_id": "C", "category": "shopping", "amount_inr": 15000,
    })
    assert resp.status_code == 200
    account = client.get("/admin/account", params={"persona_id": "C"}).json()
    assert account["balance_inr"] == 5000


def test_one_rupee_over_rejected(client):
    _set_balance(client, "C", 20000)
    resp = client.post("/transaction", json={
        "persona_id": "C", "category": "shopping", "amount_inr": 20001,
    })
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "INSUFFICIENT_BALANCE"
    account = client.get("/admin/account", params={"persona_id": "C"}).json()
    assert account["balance_inr"] == 20000


def test_zero_amount_rejected_by_schema(client):
    resp = client.post("/transaction", json={
        "persona_id": "C", "category": "shopping", "amount_inr": 0,
    })
    assert resp.status_code == 422


def test_negative_amount_rejected_by_schema(client):
    resp = client.post("/transaction", json={
        "persona_id": "C", "category": "shopping", "amount_inr": -100,
    })
    assert resp.status_code == 422


def test_rejected_transaction_does_not_mutate_persona_history(client):
    _set_balance(client, "C", 20000)
    before = client.get("/personas/C").json()["persona"]["history"]
    resp = client.post("/transaction", json={
        "persona_id": "C", "category": "shopping", "amount_inr": 25000,
    })
    assert resp.status_code == 400
    after = client.get("/personas/C").json()["persona"]["history"]
    assert before == after


def test_rejected_transaction_has_no_reason_codes_or_nudge(client):
    """
    This codebase has no UNPLANNED_EXPENSE rule code (confirmed by audit —
    rules.py defines 8 codes, none named UNPLANNED_EXPENSE). A rejected
    transaction must not run the rule engine at all, so it carries neither
    reason codes nor a nudge — the flat error body only.
    """
    _set_balance(client, "C", 20000)
    resp = client.post("/transaction", json={
        "persona_id": "C", "category": "shopping", "amount_inr": 25000,
    })
    assert resp.status_code == 400
    body = resp.json()
    assert "reason_codes" not in body
    assert "nudge" not in body
    assert "UNPLANNED_EXPENSE" not in str(body)


def test_account_credit_then_spend_new_balance_exactly(client):
    _set_balance(client, "C", 20000)
    resp = client.post("/admin/account/adjust", json={
        "persona_id": "C", "amount": 5000, "reason": "demo_credit",
    })
    assert resp.json()["balance_inr"] == 25000

    resp2 = client.post("/transaction", json={
        "persona_id": "C", "category": "shopping", "amount_inr": 25000,
    })
    assert resp2.status_code == 200
    account = client.get("/admin/account", params={"persona_id": "C"}).json()
    assert account["balance_inr"] == 0


def test_reset_restores_balance_after_a_spend(client):
    baseline = client.get("/admin/account", params={"persona_id": "C"}).json()["balance_inr"]
    client.post("/transaction", json={
        "persona_id": "C", "category": "shopping", "amount_inr": min(baseline, 100),
    })
    client.post("/reset")
    after = client.get("/admin/account", params={"persona_id": "C"}).json()["balance_inr"]
    assert after == baseline


def test_insufficient_balance_works_for_a_healthy_persona_too(client):
    """
    INSUFFICIENT_BALANCE must not depend on risk_score or spiral_detected.
    Persona A is not live, so use Persona C but force it into a LOW-looking
    balance regardless of its risk band — the rejection must still fire
    purely on the balance math.
    """
    _set_balance(client, "C", 100)
    resp = client.post("/transaction", json={
        "persona_id": "C", "category": "shopping", "amount_inr": 5000,
    })
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "INSUFFICIENT_BALANCE"


def test_arbitrary_balance_and_amount_not_hardcoded(client):
    """Same rule must hold for a completely different balance/amount pair."""
    _set_balance(client, "C", 7777)
    ok = client.post("/transaction", json={
        "persona_id": "C", "category": "shopping", "amount_inr": 7777,
    })
    assert ok.status_code == 200
    assert client.get("/admin/account", params={"persona_id": "C"}).json()["balance_inr"] == 0

    client.post("/reset")
    _set_balance(client, "C", 7777)
    rejected = client.post("/transaction", json={
        "persona_id": "C", "category": "shopping", "amount_inr": 7778,
    })
    assert rejected.status_code == 400
    assert rejected.json()["shortfall_inr"] == 1
