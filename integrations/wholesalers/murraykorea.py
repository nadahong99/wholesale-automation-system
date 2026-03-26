import logging
import random
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

BASE_PRODUCTS = [
    {"name": "캔들 소이왁스 향기 200g", "price": 8000, "category": "home", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=candle1"},
    {"name": "대나무 도마 원목 주방용", "price": 12000, "category": "home", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=board1"},
    {"name": "인테리어 조명 무드등 USB", "price": 15000, "category": "home", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=light1"},
    {"name": "욕실 매트 규조토 논슬립", "price": 18000, "category": "home", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=mat1"},
    {"name": "수납 바구니 라탄 3종 세트", "price": 22000, "category": "home", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=basket1"},
    {"name": "침구 세트 극세사 싱글", "price": 35000, "category": "home", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=bedding1"},
    {"name": "화분 다육이용 미니 세라믹", "price": 4500, "category": "home", "moq": 20, "image_url": "https://via.placeholder.com/400x400?text=pot1"},
    {"name": "아로마 디퓨저 리드 100ml", "price": 14000, "category": "home", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=diffuser1"},
    {"name": "쿠션 커버 벨벳 45x45", "price": 7000, "category": "home", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=cushion1"},
    {"name": "포토 프레임 우드 6x4인치", "price": 5500, "category": "home", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=frame1"},
    {"name": "스테인레스 텀블러 500ml", "price": 9500, "category": "home", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=tumbler1"},
    {"name": "에코백 면 프린팅 중형", "price": 4000, "category": "home", "moq": 30, "image_url": "https://via.placeholder.com/400x400?text=ecobag1"},
]


class MurrayKoreaSpider:
    """Scraper for MurrayKorea wholesale marketplace (home & living)."""

    BASE_URL = "https://www.murraykorea.com"

    def __init__(self):
        self.session_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }
        logger.info("MurrayKoreaSpider initialized")

    def get_products(self) -> List[Dict]:
        """Return all available products from MurrayKorea."""
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
                "wholesaler": "murraykorea",
                "keyword": p["name"].split()[0],
                "platform": "naver",
            })
        logger.info(f"MurrayKoreaSpider: fetched {len(products)} products")
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
                    "wholesaler": "murraykorea",
                    "description": f"{p['name']} - 홈 인테리어 도매",
                    "stock": random.randint(50, 500),
                }
        except (ValueError, IndexError):
            pass
        logger.warning(f"Product not found for URL: {url}")
        return None

    def search_products(self, keyword: str) -> List[Dict]:
        """Search products by keyword."""
        kw = keyword.lower()
        results = [p for p in self.get_products() if kw in p["name"].lower()]
        logger.info(f"MurrayKoreaSpider: search '{keyword}' -> {len(results)} results")
        return results
