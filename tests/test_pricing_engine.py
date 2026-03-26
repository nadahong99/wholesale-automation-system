# tests/test_pricing_engine.py
"""Tests for core/pricing_engine.py"""
from unittest.mock import MagicMock, patch
import pytest
from core.pricing_engine import PricingEngine


class TestPricingEngine:
    def setup_method(self):
        self.engine = PricingEngine()

    def _make_product(self, wholesale_price=10000, selling_price=12500, product_id=1):
        product = MagicMock()
        product.id = product_id
        product.name = "테스트 상품"
        product.wholesale_price = wholesale_price
        product.actual_selling_price = selling_price
        product.suggested_selling_price = selling_price
        product.coupang_product_id = None
        return product

    def test_compute_optimal_price_no_competitors(self):
        product = self._make_product()
        price = self.engine.compute_optimal_price(product, [])
        # Should return minimum viable price
        assert price == 12500

    def test_compute_optimal_price_beats_competitor(self):
        product = self._make_product(10000)
        price = self.engine.compute_optimal_price(product, [15000, 16000])
        assert price is not None
        assert price < 15000
        from utils.helpers import calculate_margin
        assert calculate_margin(10000, price) >= 20.0

    def test_compute_optimal_price_cannot_beat(self):
        product = self._make_product(10000)
        # Competitor at 11000 → can't beat profitably
        price = self.engine.compute_optimal_price(product, [11000])
        # Falls back to min viable price
        assert price == 12500

    @patch("core.pricing_engine.NaverShoppingClient.get_competitor_prices")
    def test_get_competitor_prices(self, mock_get):
        mock_get.return_value = [14000.0, 15000.0]
        prices = self.engine.get_competitor_prices("테스트 상품")
        assert prices == [14000.0, 15000.0]

    def test_update_product_price(self):
        db = MagicMock()
        product = self._make_product()
        ok = self.engine.update_product_price(db, product, 13000)
        assert ok is True

    @patch("core.pricing_engine.NaverShoppingClient.get_competitor_prices")
    def test_run_price_adjustment(self, mock_prices):
        mock_prices.return_value = [15000.0]
        db = MagicMock()

        product = self._make_product()
        from database import crud
        with patch.object(crud, "get_listed_products", return_value=[product]):
            with patch.object(crud, "update_product", return_value=product):
                with patch.object(crud, "add_price_history", return_value=None):
                    adjusted = self.engine.run_price_adjustment(db)
        assert isinstance(adjusted, int)
