# tests/test_sourcing.py
"""Tests for core/sourcing_engine.py and wholesaler scraper base."""
from unittest.mock import MagicMock, patch
import pytest
from integrations.wholesalers.base import RawProduct, BaseWholesalerClient


class ConcreteClient(BaseWholesalerClient):
    wholesaler_name = "test_wholesaler"
    base_url = "https://example.com"

    def _scrape_products(self, max_products):
        return [
            RawProduct(
                name=f"Product {i}",
                wholesale_price=10000 + i * 100,
                image_url="https://example.com/img.jpg",
                wholesaler_name=self.wholesaler_name,
            )
            for i in range(max_products)
        ]


class TestRawProduct:
    def test_creation(self):
        p = RawProduct(name="Test", wholesale_price=5000, image_url="")
        assert p.name == "Test"
        assert p.wholesale_price == 5000
        assert p.moq == 1

    def test_defaults(self):
        p = RawProduct(name="X", wholesale_price=1, image_url="")
        assert p.description == ""
        assert p.category == ""
        assert p.external_product_id == ""


class TestBaseWholesalerClient:
    def test_concrete_scrape(self):
        client = ConcreteClient()
        products = client._scrape_products(5)
        assert len(products) == 5
        assert all(isinstance(p, RawProduct) for p in products)

    def test_parse_price_valid(self):
        client = ConcreteClient()
        assert client._parse_price("12,500원") == 12500.0

    def test_parse_price_empty(self):
        client = ConcreteClient()
        assert client._parse_price("") is None

    def test_parse_price_invalid(self):
        client = ConcreteClient()
        assert client._parse_price("N/A") is None

    def test_login_no_credentials(self):
        client = ConcreteClient(username="", password="")
        result = client.login()
        assert result is False

    @patch.object(ConcreteClient, "_do_login", return_value=True)
    def test_login_success(self, mock_login):
        client = ConcreteClient(username="user", password="pass")
        assert client.login() is True
        assert client._logged_in is True


class TestSourcingEngine:
    @patch("core.sourcing_engine.DaemaetopiaClient")
    @patch("core.sourcing_engine.EasymarketClient")
    @patch("core.sourcing_engine.DaemaepartnerClient")
    @patch("core.sourcing_engine.SinsangClient")
    @patch("core.sourcing_engine.MurraykoreaClient")
    @patch("core.sourcing_engine.DalgolmartClient")
    @patch("core.sourcing_engine.SessionLocal")
    def test_run_sourcing_returns_int(
        self, mock_session, mock_dal, mock_mur, mock_sin, mock_daep, mock_easy, mock_daema
    ):
        from core.sourcing_engine import run_sourcing, CLIENTS

        # Each fake client returns 5 products
        fake_raw = [
            RawProduct(name=f"P{i}", wholesale_price=10000, image_url="", wholesaler_name="test")
            for i in range(5)
        ]
        for MockClass in [mock_daema, mock_easy, mock_daep, mock_sin, mock_mur, mock_dal]:
            instance = MockClass.return_value
            instance.wholesaler_name = "test"
            instance.scrape_products.return_value = fake_raw

        db_mock = MagicMock()
        mock_session.return_value = db_mock

        from database import crud
        with patch.object(crud, "get_or_create_wholesaler", return_value=MagicMock(id=1)):
            with patch.object(crud, "create_product", return_value=MagicMock()):
                with patch.object(crud, "get_or_create_daily_report", return_value=MagicMock(new_products_sourced=0)):
                    with patch.object(crud, "save_daily_report", return_value=None):
                        with patch("core.sourcing_engine.upload_bytes", return_value=None):
                            with patch("core.sourcing_engine._download_image", return_value=None):
                                # Patch CLIENTS list
                                with patch("core.sourcing_engine.CLIENTS", [mock_daema, mock_easy]):
                                    result = run_sourcing(target_per_wholesaler=5)
        assert isinstance(result, int)
