from backend.app.services.allocation import allocate

RATIOS = {"1": 0.6, "2": 0.3, "3": 0.1}


def test_allocation_totals_exactly_extra_amount():
    result = allocate(5000, RATIOS, risk_band="LOW", spiral_detected=False)
    total = sum(item["amount"] for item in result["allocation"])
    assert total == 5000


def test_tier1_priority_over_tier2_over_tier3_non_conservative():
    result = allocate(5000, RATIOS, risk_band="LOW", spiral_detected=False)
    by_tier = {item["tier"]: item["amount"] for item in result["allocation"]}
    assert by_tier[1] > by_tier[2] > by_tier[3]


def test_conservative_shift_when_spiral_detected():
    normal = allocate(5000, RATIOS, risk_band="LOW", spiral_detected=False)
    spiraling = allocate(5000, RATIOS, risk_band="LOW", spiral_detected=True)
    normal_by_tier = {i["tier"]: i["amount"] for i in normal["allocation"]}
    spiral_by_tier = {i["tier"]: i["amount"] for i in spiraling["allocation"]}
    assert spiral_by_tier[1] > normal_by_tier[1]
    assert spiral_by_tier[3] < normal_by_tier[3]


def test_conservative_shift_when_risk_band_high():
    result = allocate(5000, RATIOS, risk_band="HIGH", spiral_detected=False)
    total = sum(item["amount"] for item in result["allocation"])
    assert total == 5000
    by_tier = {item["tier"]: item["amount"] for item in result["allocation"]}
    assert by_tier[1] > by_tier[2] > by_tier[3]


def test_allocation_responds_to_ratio_config_change():
    default_result = allocate(5000, RATIOS, risk_band="LOW", spiral_detected=False)
    custom_ratios = {"1": 0.34, "2": 0.33, "3": 0.33}
    custom_result = allocate(5000, custom_ratios, risk_band="LOW", spiral_detected=False)
    default_by_tier = {i["tier"]: i["amount"] for i in default_result["allocation"]}
    custom_by_tier = {i["tier"]: i["amount"] for i in custom_result["allocation"]}
    assert default_by_tier[1] != custom_by_tier[1]
    assert sum(custom_by_tier.values()) == 5000


def test_priority_order_field():
    result = allocate(5000, RATIOS, risk_band="LOW", spiral_detected=False)
    assert result["priority_order"] == [1, 2, 3]


def test_suggestion_is_explainable_string():
    result = allocate(5000, RATIOS, risk_band="LOW", spiral_detected=False)
    assert "Tier 1" in result["suggestion"]
    assert "5,000" in result["suggestion"]
