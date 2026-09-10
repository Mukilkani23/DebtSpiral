def test_get_account_returns_current_user_state(client):
    resp = client.get("/admin/account", params={"persona_id": "C"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["persona_id"] == "C"
    assert data["balance_inr"] >= 0
    assert set(data["allocated"].keys()) == {"tier_1", "tier_2", "tier_3"}


def test_get_account_404_for_unknown_persona(client):
    resp = client.get("/admin/account", params={"persona_id": "Z"})
    assert resp.status_code == 404


def test_adjust_increases_balance_by_exact_amount(client):
    before = client.get("/admin/account", params={"persona_id": "C"}).json()["balance_inr"]
    resp = client.post("/admin/account/adjust", json={
        "persona_id": "C", "amount": 5000, "reason": "demo_credit",
    })
    assert resp.status_code == 200
    after = resp.json()["balance_inr"]
    assert after == round(before + 5000, 2)


def test_adjust_negative_amount_reduces_balance(client):
    client.post("/admin/account/adjust", json={"persona_id": "C", "amount": 5000, "reason": "demo_credit"})
    before = client.get("/admin/account", params={"persona_id": "C"}).json()["balance_inr"]
    resp = client.post("/admin/account/adjust", json={"persona_id": "C", "amount": -2000, "reason": "demo_debit"})
    assert resp.status_code == 200
    assert resp.json()["balance_inr"] == round(before - 2000, 2)


def test_adjust_prevents_negative_balance(client):
    resp = client.post("/admin/account/adjust", json={
        "persona_id": "C", "amount": -999999, "reason": "demo_debit",
    })
    assert resp.status_code == 400


def test_adjust_unknown_persona_404(client):
    resp = client.post("/admin/account/adjust", json={
        "persona_id": "Z", "amount": 5000, "reason": "demo_credit",
    })
    assert resp.status_code == 404


def test_reset_restores_original_account_balance(client):
    baseline = client.get("/admin/account", params={"persona_id": "C"}).json()["balance_inr"]
    client.post("/admin/account/adjust", json={"persona_id": "C", "amount": 5000, "reason": "demo_credit"})
    client.post("/reset")
    after_reset = client.get("/admin/account", params={"persona_id": "C"}).json()["balance_inr"]
    assert after_reset == baseline


def test_positive_adjustment_creates_allocation_recommendation(client):
    resp = client.post("/admin/account/adjust", json={
        "persona_id": "C", "amount": 5000, "reason": "demo_credit",
    })
    data = resp.json()
    assert data["last_allocation"] is not None
    assert data["last_allocation"]["extra_amount"] == 5000
    total = sum(item["amount"] for item in data["last_allocation"]["allocation"])
    assert total == 5000


def test_negative_adjustment_does_not_create_allocation(client):
    client.post("/admin/account/adjust", json={"persona_id": "C", "amount": 5000, "reason": "demo_credit"})
    resp = client.post("/admin/account/adjust", json={"persona_id": "C", "amount": -1000, "reason": "demo_debit"})
    data = resp.json()
    # last_allocation still reflects the prior positive adjustment, not overwritten by the debit
    assert data["last_allocation"]["extra_amount"] == 5000
