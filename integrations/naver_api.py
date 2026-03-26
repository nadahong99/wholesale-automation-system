# integrations/naver_api.py
"""Naver API integration: Datalab search trends, Shopping search."""
import json
import hmac
import hashlib
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config.settings import settings
from utils.logger import get_logger
from utils.decorators import retry_on_exception

logger = get_logger("naver_api")

DATALAB_URL = "https://openapi.naver.com/v1/datalab/search"
SHOPPING_SEARCH_URL = "https://openapi.naver.com/v1/search/shop.json"


class NaverDatalabClient:
    """Naver Datalab API – get search volume trends."""

    def __init__(self):
        self.client_id = settings.NAVER_DATALAB_CLIENT_ID
        self.client_secret = settings.NAVER_DATALAB_CLIENT_SECRET

    @retry_on_exception(retries=3, delay=2)
    def get_search_volume(self, keyword: str, period_days: int = 30) -> int:
        """Return total search count for *keyword* over the past *period_days*."""
        if not self.client_id:
            logger.warning("Naver Datalab credentials not set, returning 0.")
            return 0

        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        body = {
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "timeUnit": "date",
            "keywordGroups": [{"groupName": keyword, "keywords": [keyword]}],
        }
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "Content-Type": "application/json",
        }
        resp = requests.post(DATALAB_URL, json=body, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        total = 0
        for result in data.get("results", []):
            for dp in result.get("data", []):
                total += dp.get("ratio", 0)
        return int(total)

    def get_search_volumes_batch(self, keywords: List[str]) -> Dict[str, int]:
        """Return a mapping of keyword -> search volume for a list of keywords."""
        volumes: Dict[str, int] = {}
        for kw in keywords:
            try:
                volumes[kw] = self.get_search_volume(kw)
                time.sleep(0.3)
            except Exception as exc:
                logger.warning(f"Failed to get search volume for '{kw}': {exc}")
                volumes[kw] = 0
        return volumes


class NaverShoppingClient:
    """Naver Shopping Search API – get product counts and competitor prices."""

    def __init__(self):
        self.client_id = settings.NAVER_CLIENT_ID
        self.client_secret = settings.NAVER_CLIENT_SECRET

    @retry_on_exception(retries=3, delay=2)
    def search_products(self, keyword: str, display: int = 10, start: int = 1) -> dict:
        """Search Naver Shopping for *keyword* and return raw API response."""
        if not self.client_id:
            logger.warning("Naver Shopping API credentials not set.")
            return {}

        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        params = {
            "query": keyword,
            "display": display,
            "start": start,
            "sort": "sim",
        }
        resp = requests.get(SHOPPING_SEARCH_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def get_product_count(self, keyword: str) -> int:
        """Return total number of Naver Shopping products for *keyword*."""
        try:
            data = self.search_products(keyword, display=1)
            return int(data.get("total", 0))
        except Exception as exc:
            logger.warning(f"Failed to get product count for '{keyword}': {exc}")
            return 0

    def get_competitor_prices(self, keyword: str, top_n: int = 5) -> List[float]:
        """Return a list of the top-*n* competitor prices for *keyword*."""
        try:
            data = self.search_products(keyword, display=top_n)
            prices = []
            for item in data.get("items", []):
                try:
                    price = float(item.get("lprice", 0))
                    if price > 0:
                        prices.append(price)
                except (ValueError, TypeError):
                    pass
            return prices
        except Exception as exc:
            logger.warning(f"Failed to get competitor prices for '{keyword}': {exc}")
            return []

    def get_lowest_competitor_price(self, keyword: str) -> Optional[float]:
        """Return the lowest competitor price on Naver Shopping."""
        prices = self.get_competitor_prices(keyword)
        return min(prices) if prices else None
