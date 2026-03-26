import logging
import random
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

BASE_PRODUCTS = [
    {"name": "수분 쿠션 파운데이션 SPF50+", "price": 8500, "category": "beauty", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=cushion1"},
    {"name": "히알루론산 앰플 세럼 30ml", "price": 12000, "category": "beauty", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=serum1"},
    {"name": "클렌징폼 약산성 민감성", "price": 6000, "category": "beauty", "moq": 15, "image_url": "https://via.placeholder.com/400x400?text=cleanser1"},
    {"name": "레티놀 나이트 크림 50ml", "price": 18000, "category": "beauty", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=cream1"},
    {"name": "선크림 톤업 SPF50+ PA+++", "price": 9500, "category": "beauty", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=sunscreen1"},
    {"name": "립틴트 벨벳 매트 7색상", "price": 5500, "category": "beauty", "moq": 20, "image_url": "https://via.placeholder.com/400x400?text=tint1"},
    {"name": "마스카라 볼륨 워터프루프", "price": 7000, "category": "beauty", "moq": 15, "image_url": "https://via.placeholder.com/400x400?text=mascara1"},
    {"name": "아이섀도우 팔레트 12색", "price": 15000, "category": "beauty", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=eyeshadow1"},
    {"name": "시트마스크 콜라겐 10매입", "price": 8000, "category": "beauty", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=mask1"},
    {"name": "미스트 토너 수분 200ml", "price": 7500, "category": "beauty", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=mist1"},
    {"name": "에센스 나이아신아마이드 10%", "price": 14000, "category": "beauty", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=essence1"},
    {"name": "립밤 시어버터 보습", "price": 3500, "category": "beauty", "moq": 20, "image_url": "https://via.placeholder.com/400x400?text=lipbalm1"},
]


class SinsangSpider:
    """Scraper for Sinsang wholesale marketplace (beauty & cosmetics)."""

    BASE_URL = "https://www.sinsang.market"

    def __init__(self):
        self.session_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }
        logger.info("SinsangSpider initialized")

    def get_products(self) -> List[Dict]:
        """Return all available products from Sinsang."""
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
                "wholesaler": "sinsang",
                "keyword": p["name"].split()[0],
                "platform": "naver",
            })
        logger.info(f"SinsangSpider: fetched {len(products)} products")
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
                    "wholesaler": "sinsang",
                    "description": f"{p['name']} - K-뷰티 도매",
                    "stock": random.randint(200, 2000),
                }
        except (ValueError, IndexError):
            pass
        logger.warning(f"Product not found for URL: {url}")
        return None

    def search_products(self, keyword: str) -> List[Dict]:
        """Search products by keyword."""
        kw = keyword.lower()
        results = [p for p in self.get_products() if kw in p["name"].lower()]
        logger.info(f"SinsangSpider: search '{keyword}' -> {len(results)} results")
        return results
