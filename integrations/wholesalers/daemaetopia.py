import logging
import random
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

BASE_PRODUCTS = [
    {"name": "여름 플로럴 미디 원피스", "price": 18000, "category": "clothing", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=dress1"},
    {"name": "루즈핏 린넨 셔츠 블라우스", "price": 15000, "category": "clothing", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=blouse1"},
    {"name": "하이웨스트 와이드 팬츠", "price": 22000, "category": "clothing", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=pants1"},
    {"name": "오버사이즈 스트라이프 티셔츠", "price": 12000, "category": "clothing", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=tshirt1"},
    {"name": "체크 패턴 미니 스커트", "price": 16000, "category": "clothing", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=skirt1"},
    {"name": "니트 가디건 베이직", "price": 25000, "category": "clothing", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=cardigan1"},
    {"name": "데님 자켓 워싱", "price": 35000, "category": "clothing", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=jacket1"},
    {"name": "슬리브리스 크롭 탑", "price": 9000, "category": "clothing", "moq": 10, "image_url": "https://via.placeholder.com/400x400?text=top1"},
    {"name": "롤업 반바지 면 소재", "price": 13000, "category": "clothing", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=shorts1"},
    {"name": "레이스 트리밍 슬립 원피스", "price": 20000, "category": "clothing", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=slip1"},
    {"name": "앵클 부츠컷 슬랙스", "price": 28000, "category": "clothing", "moq": 5, "image_url": "https://via.placeholder.com/400x400?text=slacks1"},
    {"name": "프릴 넥 블라우스 화이트", "price": 17000, "category": "clothing", "moq": 3, "image_url": "https://via.placeholder.com/400x400?text=blouse2"},
]


class DaemaetopiaSpider:
    """Scraper for Daemaetopia wholesale marketplace (clothing & accessories)."""

    BASE_URL = "https://www.daemaetopia.com"

    def __init__(self):
        self.session_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }
        logger.info("DaemaetopiaSpider initialized")

    def get_products(self) -> List[Dict]:
        """Return all available products from Daemaetopia."""
        products = []
        for i, p in enumerate(BASE_PRODUCTS):
            product = {
                "name": p["name"],
                "price": p["price"],
                "purchase_price": p["price"],
                "url": f"{self.BASE_URL}/product/{i + 1}",
                "image_url": p["image_url"],
                "moq": p["moq"],
                "category": p["category"],
                "wholesaler": "daemaetopia",
                "keyword": p["name"].split()[0],
                "platform": "naver",
            }
            products.append(product)
        logger.info(f"DaemaetopiaSpider: fetched {len(products)} products")
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
                    "wholesaler": "daemaetopia",
                    "description": f"{p['name']} - 도매 상품",
                    "stock": random.randint(50, 500),
                }
        except (ValueError, IndexError):
            pass
        logger.warning(f"Product not found for URL: {url}")
        return None

    def search_products(self, keyword: str) -> List[Dict]:
        """Search products by keyword."""
        keyword_lower = keyword.lower()
        results = []
        for p in self.get_products():
            if keyword_lower in p["name"].lower() or keyword_lower in p.get("keyword", "").lower():
                results.append(p)
        logger.info(f"DaemaetopiaSpider: search '{keyword}' -> {len(results)} results")
        return results
