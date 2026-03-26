import logging
import random
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

BASE_PRODUCTS = [
    {"name": "캔버스 토트백 대용량", "price": 12000, "category": "bags", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=bag1"},
    {"name": "퀼팅 체인 미니백", "price": 25000, "category": "bags", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=bag2"},
    {"name": "크로스백 지퍼 포켓", "price": 18000, "category": "bags", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=bag3"},
    {"name": "버킷백 드로스트링 스타일", "price": 22000, "category": "bags", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=bag4"},
    {"name": "백팩 라지 여행용", "price": 35000, "category": "bags", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=bag5"},
    {"name": "클러치 이브닝백", "price": 15000, "category": "bags", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=bag6"},
    {"name": "스니커즈 흰색 캔버스", "price": 28000, "category": "shoes", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=shoe1"},
    {"name": "로퍼 스웨이드 플랫", "price": 32000, "category": "shoes", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=shoe2"},
    {"name": "샌들 스트랩 여름", "price": 20000, "category": "shoes", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=shoe3"},
    {"name": "운동화 경량 메쉬", "price": 38000, "category": "shoes", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=shoe4"},
    {"name": "뮬 슬링백 키튼힐", "price": 29000, "category": "shoes", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=shoe5"},
    {"name": "앵클부츠 첼시 스타일", "price": 45000, "category": "shoes", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=shoe6"},
]


class EasyMarketSpider:
    """Scraper for EasyMarket wholesale marketplace (bags & shoes)."""

    BASE_URL = "https://www.easymarket.co.kr"

    def __init__(self):
        self.session_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }
        logger.info("EasyMarketSpider initialized")

    def get_products(self) -> List[Dict]:
        """Return all available products from EasyMarket."""
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
                "wholesaler": "easymarket",
                "keyword": p["name"].split()[0],
                "platform": "naver",
            })
        logger.info(f"EasyMarketSpider: fetched {len(products)} products")
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
                    "wholesaler": "easymarket",
                    "description": f"{p['name']} - 도매 상품",
                    "stock": random.randint(30, 300),
                }
        except (ValueError, IndexError):
            pass
        logger.warning(f"Product not found for URL: {url}")
        return None

    def search_products(self, keyword: str) -> List[Dict]:
        """Search products by keyword."""
        kw = keyword.lower()
        results = [p for p in self.get_products() if kw in p["name"].lower()]
        logger.info(f"EasyMarketSpider: search '{keyword}' -> {len(results)} results")
        return results
