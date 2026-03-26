import hashlib
import hmac
import logging
import random
import string
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


def _random_product_id() -> str:
    return "CP" + "".join(random.choices(string.digits, k=10))


class CoupangAPI:
    """Coupang Wing API client with HMAC-SHA256 signature."""

    BASE_URL = "https://api-gateway.coupang.com"

    def __init__(
        self,
        access_key: str = "",
        secret_key: str = "",
        vendor_id: str = "",
    ):
        self.access_key = access_key
        self.secret_key = secret_key
        self.vendor_id = vendor_id
        logger.info(f"CoupangAPI initialized vendor_id={vendor_id!r}")

    def _generate_signature(
        self, method: str, uri: str, params: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Generate HMAC-SHA256 Authorization header for Coupang API."""
        datetime_str = datetime.utcnow().strftime("%y%m%dT%H%M%SZ")
        query = ""
        if params:
            query = urlencode(sorted(params.items()))
        message = f"{datetime_str}{method}{uri}{query}"
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return {
            "Authorization": (
                f"CEA algorithm=HmacSHA256, access-key={self.access_key}, "
                f"signed-date={datetime_str}, signature={signature}"
            ),
            "Content-Type": "application/json;charset=UTF-8",
        }

    def register_product(self, product_data: Dict) -> Dict:
        """Register a new product on Coupang (mock)."""
        product_id = _random_product_id()
        result = {
            "productId": product_id,
            "vendorId": self.vendor_id,
            "displayCategoryCode": "1001",
            "sellerProductName": product_data.get("name", "Unknown"),
            "vendorUserId": "seller01",
            "salePrice": product_data.get("selling_price", 0),
            "status": "APPROVED",
            "registered_at": datetime.utcnow().isoformat(),
        }
        logger.info(f"CoupangAPI: registered product '{product_data.get('name')}' id={product_id}")
        return result

    def update_product_price(self, product_id: str, new_price: int) -> Dict:
        """Update selling price of an existing Coupang product (mock)."""
        result = {
            "productId": product_id,
            "new_price": new_price,
            "status": "SUCCESS",
            "updated_at": datetime.utcnow().isoformat(),
        }
        logger.info(f"CoupangAPI: price update {product_id} -> {new_price}")
        return result

    def get_orders(self, status: str = "ACCEPT") -> List[Dict]:
        """Fetch orders from Coupang (mock implementation)."""
        orders = []
        count = random.randint(1, 5)
        for i in range(count):
            price = random.randint(15000, 80000)
            qty = random.randint(1, 3)
            orders.append({
                "orderId": f"CP-ORD-{random.randint(100000,999999)}",
                "orderStatus": status,
                "vendorId": self.vendor_id,
                "orderDate": datetime.utcnow().isoformat(),
                "items": [
                    {
                        "vendorItemId": _random_product_id(),
                        "productName": f"쿠팡 상품 {i+1}",
                        "quantity": qty,
                        "unitPrice": price,
                        "totalPrice": price * qty,
                    }
                ],
            })
        logger.info(f"CoupangAPI: fetched {len(orders)} orders with status={status}")
        return orders

    def confirm_order(self, order_id: str) -> Dict:
        """Confirm/accept an order (mock)."""
        result = {
            "orderId": order_id,
            "status": "CONFIRMED",
            "confirmed_at": datetime.utcnow().isoformat(),
        }
        logger.info(f"CoupangAPI: confirmed order {order_id}")
        return result

    def search_products(self, keyword: str) -> List[Dict]:
        """Search Coupang for competitor products (mock price-check)."""
        base_price = abs(hash(keyword)) % 40000 + 12000
        return [
            {
                "productId": f"cp_{abs(hash(keyword))+i}",
                "productName": f"{keyword} {i+1}",
                "salePrice": base_price + random.randint(-4000, 6000),
                "isRocket": i % 2 == 0,
            }
            for i in range(5)
        ]

    def get_rocket_delivery_eligibility(self, product_data: Dict) -> Dict:
        """Check if product is eligible for Coupang Rocket delivery (mock)."""
        price = product_data.get("selling_price", 0)
        eligible = price >= 10000 and product_data.get("moq", 1) >= 10
        return {
            "eligible": eligible,
            "reason": "Meets price and MOQ requirements" if eligible else "Below minimum requirements",
            "rocket_price_premium": 500 if eligible else 0,
        }
