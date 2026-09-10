def test_get_tier_config_returns_defaults(client):
    resp = client.get("/config/tiers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["category_tiers"]["food_delivery"] == 3
    assert data["category_tiers"]["travel"] == 2
    assert abs(sum(data["extra_funds_ratios"].values()) - 1.0) < 0.01


def test_update_category_tier_changes_config(client):
    resp = client.post("/config/tiers", json={"category_tiers": {"shopping": 2}})
    assert resp.status_code == 200
    assert resp.json()["category_tiers"]["shopping"] == 2

    resp2 = client.get("/config/tiers")
    assert resp2.json()["category_tiers"]["shopping"] == 2


def test_update_rejects_invalid_tier(client):
    resp = client.post("/config/tiers", json={"category_tiers": {"shopping": 5}})
    assert resp.status_code == 400


def test_update_rejects_ratios_not_summing_to_one(client):
    resp = client.post("/config/tiers", json={"extra_funds_ratios": {"1": 0.5, "2": 0.3, "3": 0.3}})
    assert resp.status_code == 400


def test_reset_restores_default_tier_config(client):
    client.post("/config/tiers", json={"category_tiers": {"shopping": 2}})
    client.post("/reset")
    resp = client.get("/config/tiers")
    assert resp.json()["category_tiers"]["shopping"] == 3


def test_tier_config_change_affects_transaction_flow(client):
    client.post("/config/tiers", json={"category_tiers": {"shopping": 1}})
    resp = client.post("/transaction", json={
        "persona_id": "C", "category": "shopping", "amount_inr": 2000,
    })
    assert resp.status_code == 200
    codes = [c["code"] for c in resp.json()["reason_codes"]]
    assert "TIER_2" not in codes
