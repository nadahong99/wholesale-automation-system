import pytest
from core.margin_calculator import MarginCalculator


@pytest.fixture
def calc():
    return MarginCalculator(naver_fee=0.055, coupang_fee=0.108, shipping_cost=3000)


def test_naver_fee_applied_correctly(calc):
    purchase = 10000
    selling = 20000
    margin = calc.calculate_margin(purchase, selling, "naver")
    expected_fee = 20000 * 0.055
    expected_profit = 20000 - 10000 - expected_fee - 3000
    expected_margin = expected_profit / 20000 * 100
    assert abs(margin - expected_margin) < 0.01


def test_coupang_fee_applied_correctly(calc):
    purchase = 10000
    selling = 20000
    margin = calc.calculate_margin(purchase, selling, "coupang")
    expected_fee = 20000 * 0.108
    expected_profit = 20000 - 10000 - expected_fee - 3000
    expected_margin = expected_profit / 20000 * 100
    assert abs(margin - expected_margin) < 0.01


def test_naver_margin_lower_than_coupang_fee_higher(calc):
    # Naver has lower fee so naver margin should be HIGHER
    m_naver = calc.calculate_margin(10000, 20000, "naver")
    m_coupang = calc.calculate_margin(10000, 20000, "coupang")
    assert m_naver > m_coupang


def test_zero_selling_price_returns_zero(calc):
    assert calc.calculate_margin(10000, 0, "naver") == 0.0


def test_negative_margin_when_selling_below_cost(calc):
    margin = calc.calculate_margin(20000, 15000, "naver")
    assert margin < 0


def test_validate_minimum_margin_passes(calc):
    assert calc.validate_minimum_margin(25.0, min_percent=20.0) is True


def test_validate_minimum_margin_fails(calc):
    assert calc.validate_minimum_margin(15.0, min_percent=20.0) is False


def test_validate_minimum_margin_exactly_at_threshold(calc):
    assert calc.validate_minimum_margin(20.0, min_percent=20.0) is True


def test_suggest_selling_price_achieves_target_margin(calc):
    purchase = 10000
    suggested = calc.suggest_selling_price(purchase, "naver", target_margin=0.25)
    actual_margin = calc.calculate_margin(purchase, suggested, "naver")
    assert actual_margin >= 25.0


def test_suggest_selling_price_naver_vs_coupang(calc):
    purchase = 10000
    p_naver = calc.suggest_selling_price(purchase, "naver", target_margin=0.25)
    p_coupang = calc.suggest_selling_price(purchase, "coupang", target_margin=0.25)
    # Coupang has higher fee, so must price higher
    assert p_coupang >= p_naver


def test_suggest_selling_price_rounded_to_100(calc):
    price = calc.suggest_selling_price(10000, "naver", 0.25)
    assert price % 100 == 0


def test_bundle_price_no_discount_below_5(calc):
    result = calc.calculate_bundle_price(10000, 3, "naver")
    assert result["discount_percent"] == 0
    assert result["unit_price"] == 10000
    assert result["total_price"] == 30000


def test_bundle_price_discount_at_5(calc):
    result = calc.calculate_bundle_price(10000, 5, "naver")
    assert result["discount_percent"] == 5
    assert result["unit_price"] == 9500
    assert result["total_price"] == 47500


def test_bundle_price_total_equals_unit_times_qty(calc):
    result = calc.calculate_bundle_price(15000, 10, "naver")
    assert result["total_price"] == result["unit_price"] * result["quantity"]


def test_bundle_price_invalid_quantity_raises(calc):
    with pytest.raises(ValueError):
        calc.calculate_bundle_price(10000, 0, "naver")


def test_fee_breakdown_contains_all_keys(calc):
    breakdown = calc.get_fee_breakdown(10000, 20000, "naver")
    expected_keys = [
        "purchase_price", "selling_price", "platform_fee", "platform_fee_rate",
        "shipping_cost", "total_cost", "profit", "margin_percent", "meets_minimum"
    ]
    for key in expected_keys:
        assert key in breakdown


def test_fee_breakdown_profit_calculation(calc):
    breakdown = calc.get_fee_breakdown(10000, 20000, "naver")
    expected_profit = 20000 - 10000 - (20000 * 0.055) - 3000
    assert abs(breakdown["profit"] - expected_profit) < 1.0


def test_fee_breakdown_meets_minimum_true(calc):
    breakdown = calc.get_fee_breakdown(5000, 20000, "naver")
    assert breakdown["meets_minimum"] is True


def test_fee_breakdown_meets_minimum_false(calc):
    breakdown = calc.get_fee_breakdown(18000, 20000, "naver")
    assert breakdown["meets_minimum"] is False


def test_calculate_net_profit_multiple_units(calc):
    profit_single = calc.calculate_net_profit(10000, 20000, "naver", 1)
    profit_ten = calc.calculate_net_profit(10000, 20000, "naver", 10)
    assert profit_ten == profit_single * 10


def test_unknown_platform_defaults_to_naver_fee(calc):
    m_unknown = calc.calculate_margin(10000, 20000, "unknown")
    m_naver = calc.calculate_margin(10000, 20000, "naver")
    assert m_unknown == m_naver


def test_suggest_selling_price_impossible_target_raises(calc):
    with pytest.raises(ValueError):
        calc.suggest_selling_price(10000, "coupang", target_margin=0.95)
