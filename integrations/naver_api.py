import hashlib
import hmac
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

MOCK_KEYWORD_VOLUMES = {
    "여름원피스": (85000, 4200),
    "니트가디건": (72000, 5800),
    "크로스백": (62000, 4900),
    "무선이어폰": (95000, 6800),
    "쿠션파운데이션": (78000, 5200),
    "에어프라이어": (112000, 8500),
    "텀블러": (58000, 9800),
    "캐리어": (45000, 3200),
    "운동화": (88000, 12000),
    "향수": (67000, 8900),
}


class NaverAPI:
    """Naver Shopping & DataLab API client with mock fallback."""

    BASE_URL = "https://openapi.naver.com/v1"

    def __init__(self, client_id: str = "", client_secret: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
        self._headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        }
        logger.info("NaverAPI initialized")

    def search_shopping(self, keyword: str, display: int = 10) -> List[Dict]:
        """Search Naver Shopping for products (mock implementation)."""
        base_price = abs(hash(keyword)) % 40000 + 10000
        products = []
        for i in range(display):
            price = base_price + random.randint(-3000, 5000)
            products.append({
                "productId": f"naver_{abs(hash(keyword))+i}",
                "title": f"{keyword} 상품 {i+1}",
                "lprice": price,
                "hprice": int(price * 1.2),
                "mallName": f"쇼핑몰{i+1}",
                "image": f"https://via.placeholder.com/200x200?text={keyword}_{i+1}",
                "link": f"https://shopping.naver.com/product/{abs(hash(keyword))+i}",
                "category1": "패션의류",
                "maker": f"브랜드{i+1}",
            })
        logger.info(f"NaverAPI: search '{keyword}' -> {len(products)} results")
        return products

    def get_datalab_trend(
        self,
        keywords: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict:
        """Get search trend data for keywords (mock implementation)."""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        result: Dict = {"startDate": start_date, "endDate": end_date, "timeUnit": "date", "results": []}
        for keyword in keywords:
            base_volume, _ = MOCK_KEYWORD_VOLUMES.get(keyword, (random.randint(10000, 100000), 1000))
            data_points = []
            current_date = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            while current_date <= end:
                ratio = round(random.uniform(60, 100), 2)
                data_points.append({"period": current_date.strftime("%Y-%m-%d"), "ratio": ratio})
                current_date += timedelta(days=1)
            result["results"].append({"title": keyword, "data": data_points})
        return result

    def get_keyword_stats(self, keyword: str) -> Dict:
        """Get search volume and product count statistics for a keyword."""
        search_volume, product_count = MOCK_KEYWORD_VOLUMES.get(
            keyword,
            (random.randint(5000, 120000), random.randint(500, 15000)),
        )
        # Add some randomness
        search_volume = int(search_volume * random.uniform(0.9, 1.1))
        product_count = int(product_count * random.uniform(0.9, 1.1))
        ratio = round(search_volume / max(product_count, 1), 2)
        return {
            "keyword": keyword,
            "search_volume": search_volume,
            "product_count": product_count,
            "ratio": ratio,
            "is_golden": ratio >= 10,
            "checked_at": datetime.utcnow().isoformat(),
        }

    def is_golden_keyword(self, keyword: str) -> bool:
        """Return True if keyword has search_volume/product_count ratio >= 10."""
        stats = self.get_keyword_stats(keyword)
        return stats["is_golden"]

    def search_products_for_price_check(self, product_name: str) -> List[Dict]:
        """Return competitor prices for price-checking purposes."""
        return self.search_shopping(product_name, display=5)

    def batch_keyword_stats(self, keywords: List[str]) -> List[Dict]:
        """Get stats for multiple keywords at once."""
        return [self.get_keyword_stats(kw) for kw in keywords]
