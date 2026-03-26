# tests/test_order_processor.py
"""Tests for core/order_processor.py"""
from unittest.mock import MagicMock, patch
import pytest
from core.order_processor import process_customer_order, _place_wholesale_order, auto_list_product


def _make_product(moq=1, product_id=1, wholesale_price=10000, selling_price=12500):
    p = MagicMock()
    p.id = product_id
    p.name = "테스트 상품"
    p.moq = moq
    p.wholesale_price = wholesale_price
    p.actual_selling_price = selling_price
    p.suggested_selling_price = selling_price
    p.wholesaler_id = 1
    p.gcs_image_url = None
    p.image_url = ""
    p.description = ""
    p.coupang_product_id = None
    return p


class TestProcessCustomerOrder:
    @patch("core.order_processor.crud.get_product")
    @patch("core.order_processor.crud.create_order")
    @patch("core.order_processor.crud.update_order")
    def test_moq_1_places_direct_order(self, mock_update, mock_create, mock_get):
        product = _make_product(moq=1)
        mock_get.return_value = product
        order = MagicMock(id=1, quantity=1, total_price=12500, customer_order_id="C001")
        mock_create.return_value = order

        db = MagicMock()
        result = process_customer_order(db, 1, "C001", 1)
        assert result is not None
        mock_update.assert_called_once()

    @patch("core.order_processor.crud.get_product")
    @patch("core.order_processor.crud.create_order")
    @patch("core.order_processor.crud.update_order")
    def test_moq_5_places_bundle_order(self, mock_update, mock_create, mock_get):
        product = _make_product(moq=5)
        mock_get.return_value = product
        order = MagicMock(id=2, quantity=5, total_price=62500, customer_order_id="C002")
        mock_create.return_value = order

        db = MagicMock()
        result = process_customer_order(db, 1, "C002", 5)
        assert result is not None
        mock_update.assert_called_once()

    @patch("core.order_processor.crud.get_product")
    @patch("core.order_processor.crud.create_order")
    @patch("core.order_processor.send_message")
    def test_moq_10_triggers_ceo_review(self, mock_send, mock_create, mock_get):
        product = _make_product(moq=10)
        mock_get.return_value = product
        order = MagicMock(id=3, quantity=10, total_price=125000, customer_order_id="C003")
        mock_create.return_value = order

        db = MagicMock()
        process_customer_order(db, 1, "C003", 10)
        mock_send.assert_called_once()

    @patch("core.order_processor.crud.get_product", return_value=None)
    def test_product_not_found(self, mock_get):
        db = MagicMock()
        result = process_customer_order(db, 999, "C999", 1)
        assert result is None


class TestAutoListProduct:
    @patch("core.order_processor.crud.get_product")
    @patch("core.order_processor.crud.update_product")
    def test_auto_list_marks_product_listed(self, mock_update, mock_get):
        product = _make_product()
        mock_get.return_value = product

        db = MagicMock()
        with patch("core.order_processor.CoupangClient") as mock_coupang:
            mock_coupang.return_value.build_product_payload.return_value = {}
            mock_coupang.return_value.create_product.return_value = {}
            result = auto_list_product(db, 1)

        assert result is True
        mock_update.assert_called()

    @patch("core.order_processor.crud.get_product", return_value=None)
    def test_auto_list_product_not_found(self, mock_get):
        db = MagicMock()
        result = auto_list_product(db, 999)
        assert result is False
