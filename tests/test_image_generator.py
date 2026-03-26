# tests/test_image_generator.py
"""Tests for core/image_generator.py"""
from unittest.mock import patch, MagicMock
import io
import pytest
from core.image_generator import (
    download_image,
    make_white_background,
    make_thumbnail,
    add_price_overlay,
    process_product_image,
)


class TestDownloadImage:
    @patch("core.image_generator.requests.get")
    def test_download_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = b"fake_image_data"
        mock_get.return_value = mock_resp
        result = download_image("https://example.com/img.jpg")
        assert result == b"fake_image_data"

    @patch("core.image_generator.requests.get", side_effect=Exception("timeout"))
    def test_download_failure_returns_none(self, mock_get):
        result = download_image("https://example.com/img.jpg")
        assert result is None

    def test_empty_url_returns_none(self):
        result = download_image("")
        assert result is None


class TestImageProcessing:
    def _make_jpeg_bytes(self):
        """Create a minimal valid JPEG bytes object using Pillow."""
        try:
            from PIL import Image
            img = Image.new("RGB", (100, 100), color=(255, 0, 0))
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            return buf.getvalue()
        except ImportError:
            pytest.skip("Pillow not installed")

    def test_make_thumbnail_returns_bytes(self):
        jpeg = self._make_jpeg_bytes()
        result = make_thumbnail(jpeg, size=(50, 50))
        assert result is not None
        assert isinstance(result, bytes)

    def test_make_white_background(self):
        jpeg = self._make_jpeg_bytes()
        result = make_white_background(jpeg)
        assert isinstance(result, bytes)

    def test_add_price_overlay(self):
        jpeg = self._make_jpeg_bytes()
        result = add_price_overlay(jpeg, selling_price=12500, margin_percent=20.0)
        assert isinstance(result, bytes)

    def test_process_product_image_no_url(self):
        main, thumb = process_product_image("", 12500, 20.0)
        assert main is None
        assert thumb is None

    @patch("core.image_generator.download_image")
    def test_process_product_image_with_url(self, mock_dl):
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("Pillow not installed")

        img = Image.new("RGB", (100, 100), color=(0, 255, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        mock_dl.return_value = buf.getvalue()

        main, thumb = process_product_image("https://example.com/x.jpg", 12500, 20.0)
        assert main is not None
        assert thumb is not None
