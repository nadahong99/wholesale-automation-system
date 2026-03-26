# tests/test_margin_calculator.py
"""Tests for core/margin_calculator.py"""
import pytest
from core.margin_calculator import MarginCalculator, GoldenKeywordFilter
from utils.helpers import calculate_margin, calculate_selling_price


class TestMarginCalculator:
    def setup_method(self):
        self.calc = MarginCalculator(min_margin_percent=20.0)

    def test_compute_selling_price_basic(self):
        # 20% margin: selling = wholesale / 0.8
        price = self.calc.compute_selling_price(10000)
        assert price == 12500

    def test_compute_selling_price_rounds_to_won(self):
        price = self.calc.compute_selling_price(9999)
        assert isinstance(price, int)
        assert price >= 9999

    def test_compute_margin(self):
        margin = self.calc.compute_margin(10000, 12500)
        assert abs(margin - 20.0) < 0.01

    def test_is_margin_ok_true(self):
        assert self.calc.is_margin_ok(10000, 12500) is True

    def test_is_margin_ok_false(self):
        assert self.calc.is_margin_ok(10000, 11000) is False

    def test_adjust_price_beats_competitor(self):
        # Competitor sells at 15000, wholesale=10000, so we can beat at 14850 (>20%)
        adjusted = self.calc.adjust_price_for_competitor(10000, 15000)
        assert adjusted is not None
        margin = self.calc.compute_margin(10000, adjusted)
        assert margin >= 20.0
        assert adjusted < 15000

    def test_adjust_price_cannot_compete(self):
        # Competitor at 11000, wholesale=10000 → margin would be ~9%
        result = self.calc.adjust_price_for_competitor(10000, 11000)
        # Should return minimum viable price (12500), not None
        assert result is not None
        assert result >= self.calc.compute_selling_price(10000)

    def test_zero_wholesale_price(self):
        price = self.calc.compute_selling_price(0)
        assert price == 0

    def test_high_margin_target(self):
        calc50 = MarginCalculator(min_margin_percent=50.0)
        price = calc50.compute_selling_price(10000)
        assert price == 20000

    def test_margin_calculation_helper(self):
        assert abs(calculate_margin(8000, 10000) - 20.0) < 0.01

    def test_selling_price_helper(self):
        assert calculate_selling_price(10000, 20.0) == 12500


class TestGoldenKeywordFilter:
    def setup_method(self):
        self.gk = GoldenKeywordFilter(threshold=10.0)

    def _make_product(self, sv, pc):
        return {"product_id": 1, "name": "test", "search_volume": sv, "product_count_in_market": pc}

    def test_score_calculation(self):
        score = self.gk.calculate_score(1000, 100)
        assert score == 10.0

    def test_is_golden_true(self):
        assert self.gk.is_golden(1000, 50) is True

    def test_is_golden_false(self):
        assert self.gk.is_golden(100, 100) is False

    def test_is_golden_zero_product_count(self):
        # Should not raise ZeroDivisionError
        assert self.gk.is_golden(1000, 0) is True

    def test_filter_products_empty(self):
        result = self.gk.filter_products([], min_results=0, max_results=10)
        assert result == []

    def test_filter_products_selects_high_scores(self):
        products = [
            {"product_id": i, "search_volume": i * 100, "product_count_in_market": 10}
            for i in range(1, 11)
        ]
        result = self.gk.filter_products(products, min_results=0, max_results=100)
        # score = i*100/10 = i*10 → all i>=1 yield score ≥10
        assert all(r["golden_keyword_score"] >= 10.0 for r in result)

    def test_filter_products_sorted_descending(self):
        products = [
            {"product_id": 1, "search_volume": 200, "product_count_in_market": 10},
            {"product_id": 2, "search_volume": 500, "product_count_in_market": 10},
            {"product_id": 3, "search_volume": 300, "product_count_in_market": 10},
        ]
        result = self.gk.filter_products(products, min_results=0)
        scores = [r["golden_keyword_score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_filter_products_max_results(self):
        products = [
            {"product_id": i, "search_volume": 1000, "product_count_in_market": 10}
            for i in range(200)
        ]
        result = self.gk.filter_products(products, min_results=0, max_results=50)
        assert len(result) <= 50
