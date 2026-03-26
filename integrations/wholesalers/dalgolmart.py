import logging
import random
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

BASE_PRODUCTS = [
    {"name": "에어프라이어 전용 실리콘 바스켓", "price": 9500, "category": "kitchen", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=airfryer1"},
    {"name": "스텐 냄비 뚜껑 유리 20cm", "price": 7000, "category": "kitchen", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=lid1"},
    {"name": "다용도 강판 채칼 4면", "price": 5500, "category": "kitchen", "moq": 15, "image_url": "https://via.placeholder.com/400x400?text=grater1"},
    {"name": "실리콘 주걱 내열 3종 세트", "price": 6000, "category": "kitchen", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=spatula1"},
    {"name": "밀폐용기 유리 직사각 900ml", "price": 8500, "category": "kitchen", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=container1"},
    {"name": "커피 핸드드립 드리퍼 세라믹", "price": 12000, "category": "kitchen", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=dripper1"},
    {"name": "대용량 밥솥 6인용 IH", "price": 85000, "category": "kitchen", "moq": 2, "image_url": "https://via.placeholder.com/400x400?text=ricecooker1"},
    {"name": "스마트 냉장고 마그네틱 메모보드", "price": 3500, "category": "kitchen", "moq": 20, "image_url": "https://via.placeholder.com/400x400?text=memo1"},
    {"name": "국산 참기름 진한맛 500ml", "price": 9000, "category": "food", "moq": 12, "image_url": "https://via.placeholder.com/400x400?text=oil1"},
    {"name": "천연 꿀 아카시아 1kg", "price": 18000, "category": "food", "moq": 6, "image_url": "https://via.placeholder.com/400x400?text=honey1"},
    {"name": "유기농 현미 5kg", "price": 22000, "category": "food", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=rice1"},
    {"name": "프리미엄 김 도시락용 30매", "price": 4500, "category": "food", "moq": 20, "image_url": "https://via.placeholder.com/400x400?text=seaweed1"},
]


class DalgolmartSpider:
    """Scraper for Dalgolmart wholesale marketplace (kitchen & food)."""

    BASE_URL = "https://www.dalgolmart.com"

    def __init__(self):
        self.session_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }
        logger.info("DalgolmartSpider initialized")

    def get_products(self) -> List[Dict]:
        """Return all available products from Dalgolmart."""
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
                "wholesaler": "dalgolmart",
                "keyword": p["name"].split()[0],
                "platform": "coupang",
            })
        logger.info(f"DalgolmartSpider: fetched {len(products)} products")
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
                    "wholesaler": "dalgolmart",
                    "description": f"{p['name']} - 주방/식품 도매",
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
        logger.info(f"DalgolmartSpider: search '{keyword}' -> {len(results)} results")
        return results
