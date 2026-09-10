"""
Regression suite: confirms the pre-existing golden demo path still works
after adding the account/allocation/tier-config extension.
"""


def test_health_still_reports_model_loaded(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_loaded"] is True
    assert data["personas_loaded"] == 5


def test_personas_list_still_works(client):
    resp = client.get("/personas")
    assert resp.status_code == 200
    ids = {p["persona_id"] for p in resp.json()}
    assert ids == {"A", "B", "C", "D", "E"}


def test_persona_c_detail_still_works(client):
    resp = client.get("/personas/C")
    assert resp.status_code == 200
    data = resp.json()
    assert data["persona"]["persona_id"] == "C"
    assert "risk_score" in data["assessment"]


def test_score_endpoint_still_works(client):
    resp = client.post("/score", json={"persona_id": "C"})
    assert resp.status_code == 200
    assert "risk_score" in resp.json()


def test_transaction_still_flags_persona_c_food_delivery(client):
    resp = client.post("/transaction", json={
        "persona_id": "C", "category": "food_delivery", "amount_inr": 2000,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["flagged"] is True
    assert len(data["reason_codes"]) >= 1
    assert data["nudge"] is not None


def test_transaction_on_non_live_persona_returns_403(client):
    resp = client.post("/transaction", json={
        "persona_id": "A", "category": "food_delivery", "amount_inr": 2000,
    })
    assert resp.status_code == 403


def test_transaction_unknown_persona_404(client):
    resp = client.post("/transaction", json={
        "persona_id": "Z", "category": "food_delivery", "amount_inr": 2000,
    })
    assert resp.status_code == 404


def test_project_endpoint_still_works(client):
    resp = client.post("/project", json={
        "persona_id": "C",
        "levers": {"discretionary_reduction_inr": 3000, "repayment_increase_inr": 0, "stc_reduction_count": 0},
    })
    assert resp.status_code == 200
    data = resp.json()
    for h in range(3):
        assert data["scenario_b"]["debt"][h] <= data["scenario_a"]["debt"][h]


def test_reset_restores_baseline(client):
    client.post("/transaction", json={
        "persona_id": "C", "category": "food_delivery", "amount_inr": 2000,
    })
    resp = client.post("/reset")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_no_client_controlled_risk_fields_accepted(client):
    resp = client.post("/transaction", json={
        "persona_id": "C", "category": "food_delivery", "amount_inr": 2000,
        "risk_score": 999, "flagged": False,
    })
    assert resp.status_code == 422
