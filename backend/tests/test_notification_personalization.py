"""
Integration tests: person-specific WhatsApp/nudge messages derived from
this persona's ACTUAL tier config + category spend history, via the real
POST /transaction and POST /config/tiers endpoints. Persona C is the only
`is_live` persona, so it's used throughout — Persona A/B/D differences are
covered as pure unit tests in test_message_builder.py instead.
"""


def _set_budget(client, category, amount):
    resp = client.post("/config/tiers", json={"category_budgets": {category: amount}})
    assert resp.status_code == 200
    return resp.json()


def test_budget_exceeded_message_uses_real_backend_numbers(client):
    _set_budget(client, "food_delivery", 3000)
    r1 = client.post("/transaction", json={
        "persona_id": "C", "category": "food_delivery", "amount_inr": 1000,
    })
    assert r1.status_code == 200

    r2 = client.post("/transaction", json={
        "persona_id": "C", "category": "food_delivery", "amount_inr": 2500,
    })
    assert r2.status_code == 200
    nudge = r2.json()["nudge"]
    assert nudge is not None
    msg = nudge["message"]
    assert "over your planned limit" in msg
    assert "₹3,000" in msg
    assert "₹3,500" in msg
    assert "₹500" in msg
    assert "Food Delivery" in msg


def test_near_limit_message_before_exceeding(client):
    _set_budget(client, "food_delivery", 3000)
    client.post("/transaction", json={
        "persona_id": "C", "category": "food_delivery", "amount_inr": 100,
    })
    r = client.post("/transaction", json={
        "persona_id": "C", "category": "food_delivery", "amount_inr": 2600,
    })
    assert r.status_code == 200
    nudge = r.json()["nudge"]
    assert nudge is not None
    msg = nudge["message"]
    assert "remains" in msg.lower()
    assert "over your planned limit" not in msg


def test_tier_config_change_changes_the_generated_message(client):
    """The exact demo scenario: changing Food Delivery's allocation changes
    the next notification's numbers automatically."""
    _set_budget(client, "food_delivery", 3000)
    client.post("/transaction", json={
        "persona_id": "C", "category": "food_delivery", "amount_inr": 100,
    })
    r1 = client.post("/transaction", json={
        "persona_id": "C", "category": "food_delivery", "amount_inr": 3400,
    })
    msg1 = r1.json()["nudge"]["message"]
    assert "over your planned limit" in msg1
    assert "₹3,000" in msg1
    assert "₹3,500" in msg1

    client.post("/reset")
    _set_budget(client, "food_delivery", 6000)
    client.post("/transaction", json={
        "persona_id": "C", "category": "food_delivery", "amount_inr": 100,
    })
    r2 = client.post("/transaction", json={
        "persona_id": "C", "category": "food_delivery", "amount_inr": 6400,
    })
    msg2 = r2.json()["nudge"]["message"]
    assert "over your planned limit" in msg2
    assert "₹6,000" in msg2
    assert "₹6,500" in msg2
    assert msg1 != msg2


def test_new_category_detected_on_first_spend(client):
    r = client.post("/transaction", json={
        "persona_id": "C", "category": "electronics", "amount_inr": 1000,
    })
    assert r.status_code == 200
    nudge = r.json()["nudge"]
    assert nudge is not None
    assert "new spending category" in nudge["message"]


def test_amount_anomaly_detected_after_stable_history(client):
    _set_budget(client, "subscription", 50000)
    for amt in [500, 520, 480, 510]:
        client.post("/transaction", json={
            "persona_id": "C", "category": "subscription", "amount_inr": amt,
        })
    r = client.post("/transaction", json={
        "persona_id": "C", "category": "subscription", "amount_inr": 5000,
    })
    assert r.status_code == 200
    nudge = r.json()["nudge"]
    assert nudge is not None
    assert "significantly above" in nudge["message"]


def test_tier3_restricted_message(client):
    _set_budget(client, "entertainment", 0)
    client.post("/transaction", json={
        "persona_id": "C", "category": "entertainment", "amount_inr": 100,
    })
    r = client.post("/transaction", json={
        "persona_id": "C", "category": "entertainment", "amount_inr": 8000,
    })
    assert r.status_code == 200
    nudge = r.json()["nudge"]
    assert nudge is not None
    assert "Tier 3" in nudge["message"]


def test_reset_clears_category_spend_history(client):
    client.post("/transaction", json={
        "persona_id": "C", "category": "electronics", "amount_inr": 1000,
    })
    client.post("/reset")
    r = client.post("/transaction", json={
        "persona_id": "C", "category": "electronics", "amount_inr": 1000,
    })
    assert r.status_code == 200
    nudge = r.json()["nudge"]
    assert nudge is not None
    assert "new spending category" in nudge["message"]


def test_category_budget_config_visible_via_get(client):
    resp = client.get("/config/tiers")
    assert resp.status_code == 200
    assert "category_budgets" in resp.json()
    assert resp.json()["category_budgets"]["food_delivery"] == 3000


def test_client_cannot_supply_notification_context_fields(client):
    """Frontend must never be trusted with allocated_amount/spent_amount/etc
    as transaction inputs — extra="forbid" on TransactionRequest rejects
    any attempt to smuggle them in."""
    resp = client.post("/transaction", json={
        "persona_id": "C", "category": "food_delivery", "amount_inr": 500,
        "allocated_amount_inr": 1, "spent_amount_inr": 1,
    })
    assert resp.status_code == 422
