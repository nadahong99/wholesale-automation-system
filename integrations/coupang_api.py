# integrations/coupang_api.py
"""Coupang API integration for product listing and price monitoring."""
import hmac
import hashlib
import datetime
import json
import requests
from typing import Dict, List, Optional
from config.settings import settings
from utils.logger import get_logger
from utils.decorators import retry_on_exception

logger = get_logger("coupang_api")

COUPANG_BASE_URL = "https://api-gateway.coupang.com"


def _generate_hmac(method: str, path: str, secret_key: str, access_key: str) -> str:
    """Generate Coupang HMAC Authorization header value."""
    dt = datetime.datetime.utcnow()
    timestamp = dt.strftime("%y%m%dT%H%M%SZ")
    message = f"{timestamp}{method}{path}"
    signature = hmac.new(
        secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={timestamp}, signature={signature}"


class CoupangClient:
    """Client for Coupang Open API."""

    def __init__(self):
        self.access_key = settings.COUPANG_ACCESS_KEY
        self.secret_key = settings.COUPANG_SECRET_KEY
        self.vendor_id = settings.COUPANG_VENDOR_ID

    def _get_headers(self, method: str, path: str) -> Dict[str, str]:
        auth = _generate_hmac(method, path, self.secret_key, self.access_key)
        return {
            "Authorization": auth,
            "Content-Type": "application/json",
        }

    @retry_on_exception(retries=3, delay=2)
    def create_product(self, product_data: dict) -> dict:
        """List a product on Coupang. Returns API response."""
        if not self.access_key:
            logger.warning("Coupang API credentials not set.")
            return {}
        path = f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"
        headers = self._get_headers("POST", path)
        resp = requests.post(
            COUPANG_BASE_URL + path, json=product_data, headers=headers, timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    @retry_on_exception(retries=3, delay=2)
    def update_price(self, product_id: str, new_price: float) -> bool:
        """Update the price of an already-listed Coupang product."""
        if not self.access_key:
            logger.warning("Coupang API credentials not set.")
            return False
        path = (
            f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"
            f"/{product_id}/prices"
        )
        headers = self._get_headers("PUT", path)
        payload = {"price": int(new_price)}
        resp = requests.put(
            COUPANG_BASE_URL + path, json=payload, headers=headers, timeout=30
        )
        return resp.status_code == 200

    @retry_on_exception(retries=3, delay=2)
    def get_product_price(self, product_id: str) -> Optional[float]:
        """Retrieve the current listed price of a Coupang product."""
        if not self.access_key:
            return None
        path = f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{product_id}"
        headers = self._get_headers("GET", path)
        resp = requests.get(COUPANG_BASE_URL + path, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            try:
                return float(data["data"]["salePrice"])
            except (KeyError, TypeError):
                pass
        return None

    def build_product_payload(
        self, name: str, selling_price: float, image_url: str, description: str = ""
    ) -> dict:
        """Build a minimal Coupang product creation payload."""
        return {
            "vendorId": self.vendor_id,
            "vendorUserId": self.vendor_id,
            "sellerProductName": name,
            "displayCategoryCode": 56137,  # 기타 카테고리
            "productType": 1,
            "items": [
                {
                    "itemName": name,
                    "originalPrice": int(selling_price * 1.1),
                    "salePrice": int(selling_price),
                    "maximumBuyCount": 99,
                    "maximumBuyForPerson": 0,
                    "images": [{"imageOrder": 0, "imageType": "REPRESENTATION", "cdnPath": image_url}],
                }
            ],
        }
