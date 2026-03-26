import logging
import random
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

BASE_PRODUCTS = [
    {"name": "무선 블루투스 이어폰 5.0", "price": 15000, "category": "electronics", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=earphone1"},
    {"name": "USB-C 고속 충전 케이블 1m", "price": 3500, "category": "electronics", "moq": 20, "image_url": "https://via.placeholder.com/400x400?text=cable1"},
    {"name": "스마트폰 거치대 차량용", "price": 8000, "category": "electronics", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=holder1"},
    {"name": "10000mAh 보조배터리 슬림", "price": 18000, "category": "electronics", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=battery1"},
    {"name": "무선 충전 패드 15W", "price": 12000, "category": "electronics", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=charger1"},
    {"name": "스마트워치 호환 실리콘 밴드", "price": 4500, "category": "electronics", "moq": 20, "image_url": "https://via.placeholder.com/400x400?text=band1"},
    {"name": "노이즈캔슬링 헤드폰 접이식", "price": 35000, "category": "electronics", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=headphone1"},
    {"name": "미니 블루투스 스피커 방수", "price": 22000, "category": "electronics", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=speaker1"},
    {"name": "스마트폰 케이스 투명 방탄", "price": 2500, "category": "electronics", "moq": 30, "image_url": "https://via.placeholder.com/400x400?text=case1"},
    {"name": "USB 허브 4포트 멀티", "price": 9500, "category": "electronics", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=hub1"},
    {"name": "웹캠 1080P 자동초점", "price": 28000, "category": "electronics", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=webcam1"},
    {"name": "기계식 키보드 텐키리스", "price": 45000, "category": "electronics", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=keyboard1"},
]


class DaemaepartnerSpider:
    """Scraper for Daemaepartner wholesale marketplace (electronics accessories)."""

    BASE_URL = "https://www.daemaepartner.com"

    def __init__(self):
        self.session_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }
        logger.info("DaemaepartnerSpider initialized")

    def get_products(self) -> List[Dict]:
        """Return all available products from Daemaepartner."""
        products = []
        for i, p in enumerate(BASE_PRODUCTS):
            products.append({
                "name": p["name"],
                "price": p["price"],
                "purchase_price": p["price"],
                "url": f"{self.BASE_URL}/product/{i + 1}",
                "image_url": p["image_url"],
                "moq": p["moq"],
                "category": p["category"],
                "wholesaler": "daemaepartner",
                "keyword": p["name"].split()[0],
                "platform": "coupang",
            })
        logger.info(f"DaemaepartnerSpider: fetched {len(products)} products")
        return products

    def get_product_detail(self, url: str) -> Optional[Dict]:
        """Return detail for a specific product URL."""
        try:
            idx = int(url.rstrip("/").split("/")[-1]) - 1
            if 0 <= idx < len(BASE_PRODUCTS):
                p = BASE_PRODUCTS[idx]
                return {
                    "name": p["name"],
                    "price": p["price"],
                    "purchase_price": p["price"],
                    "url": url,
                    "image_url": p["image_url"],
                    "moq": p["moq"],
                    "category": p["category"],
                    "wholesaler": "daemaepartner",
                    "description": f"{p['name']} - 전자제품 도매",
                    "stock": random.randint(100, 1000),
                }
        except (ValueError, IndexError):
            pass
        logger.warning(f"Product not found for URL: {url}")
        return None

    def search_products(self, keyword: str) -> List[Dict]:
        """Search products by keyword."""
        kw = keyword.lower()
        results = [p for p in self.get_products() if kw in p["name"].lower()]
        logger.info(f"DaemaepartnerSpider: search '{keyword}' -> {len(results)} results")
        return results
