from backend.app.services.message_builder import build_message


def test_tier_budget_exceeded_uses_real_numbers_not_hardcoded():
    result = build_message({
        "category": "food_delivery", "tier": 3, "transaction_amount_inr": 500,
        "allocated_amount_inr": 3000, "spent_amount_inr": 3500, "remaining_amount_inr": 0,
        "overage_amount_inr": 500, "is_new_category": False, "is_amount_anomaly": False,
    })
    assert result["event_type"] == "TIER_BUDGET_EXCEEDED"
    assert "₹3,000" in result["message"]
    assert "₹3,500" in result["message"]
    assert "₹500" in result["message"]
    assert "Food Delivery" in result["message"]


def test_near_limit_shows_remaining_not_overage():
    result = build_message({
        "category": "food_delivery", "tier": 3, "transaction_amount_inr": 2700,
        "allocated_amount_inr": 3000, "spent_amount_inr": 2700, "remaining_amount_inr": 300,
        "overage_amount_inr": 0, "is_new_category": False, "is_amount_anomaly": False,
    })
    assert result["event_type"] == "TIER_BUDGET_NEAR_LIMIT"
    assert "₹300" in result["message"]
    assert "remains" in result["message"].lower()
    assert "over your planned limit" not in result["message"]


def test_different_users_produce_different_messages():
    persona_a_context = {
        "category": "food_delivery", "tier": 2, "transaction_amount_inr": 500,
        "allocated_amount_inr": 8000, "spent_amount_inr": 2000, "remaining_amount_inr": 6000,
        "overage_amount_inr": 0, "is_new_category": False, "is_amount_anomaly": False,
    }
    persona_c_context = {
        "category": "food_delivery", "tier": 3, "transaction_amount_inr": 500,
        "allocated_amount_inr": 3000, "spent_amount_inr": 3500, "remaining_amount_inr": 0,
        "overage_amount_inr": 500, "is_new_category": False, "is_amount_anomaly": False,
    }
    msg_a = build_message(persona_a_context)
    msg_c = build_message(persona_c_context)
    assert msg_a["event_type"] == "GENERIC"
    assert msg_c["event_type"] == "TIER_BUDGET_EXCEEDED"
    assert msg_a["message"] != msg_c["message"]


def test_persona_b_large_shopping_overage():
    result = build_message({
        "category": "shopping", "tier": 3, "transaction_amount_inr": 12000,
        "allocated_amount_inr": 30000, "spent_amount_inr": 42000, "remaining_amount_inr": 0,
        "overage_amount_inr": 12000, "is_new_category": False, "is_amount_anomaly": False,
    })
    assert result["event_type"] == "TIER_BUDGET_EXCEEDED"
    assert "₹30,000" in result["message"]
    assert "₹42,000" in result["message"]
    assert "₹12,000" in result["message"]


def test_new_category_message():
    result = build_message({
        "category": "electronics", "tier": 2, "transaction_amount_inr": 4000,
        "allocated_amount_inr": 5000, "spent_amount_inr": 4000, "remaining_amount_inr": 1000,
        "overage_amount_inr": 0, "is_new_category": True, "is_amount_anomaly": False,
    })
    assert result["event_type"] == "UNPLANNED_EXPENSE"
    assert "new spending category" in result["message"]
    assert "Electronics" in result["message"]


def test_amount_anomaly_message_without_overage():
    result = build_message({
        "category": "travel", "tier": 2, "transaction_amount_inr": 2500,
        "allocated_amount_inr": 3000, "spent_amount_inr": 2500, "remaining_amount_inr": 500,
        "overage_amount_inr": 0, "is_new_category": False, "is_amount_anomaly": True,
    })
    assert result["event_type"] == "UNPLANNED_EXPENSE"
    assert "significantly above" in result["message"]


def test_overage_takes_priority_over_new_category_and_anomaly():
    result = build_message({
        "category": "shopping", "tier": 3, "transaction_amount_inr": 20000,
        "allocated_amount_inr": 4000, "spent_amount_inr": 24000, "remaining_amount_inr": 0,
        "overage_amount_inr": 20000, "is_new_category": True, "is_amount_anomaly": True,
    })
    assert result["event_type"] == "TIER_BUDGET_EXCEEDED"


def test_tier3_restricted_message():
    result = build_message({
        "category": "entertainment", "tier": 3, "transaction_amount_inr": 8000,
        "allocated_amount_inr": 0, "spent_amount_inr": 8000, "remaining_amount_inr": 0,
        "overage_amount_inr": 0, "is_new_category": False, "is_amount_anomaly": False,
    })
    assert result["event_type"] == "RESTRICTED_SPEND"
    assert "Tier 3" in result["message"]
    assert "Entertainment" in result["message"]
    assert "₹8,000" in result["message"]


def test_generic_when_nothing_notable():
    result = build_message({
        "category": "travel", "tier": 2, "transaction_amount_inr": 200,
        "allocated_amount_inr": 3000, "spent_amount_inr": 200, "remaining_amount_inr": 2800,
        "overage_amount_inr": 0, "is_new_category": False, "is_amount_anomaly": False,
    })
    assert result["event_type"] == "GENERIC"
    assert result["message"] == ""
