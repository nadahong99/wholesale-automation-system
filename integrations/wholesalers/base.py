# integrations/wholesalers/base.py
"""Base class for all wholesaler scrapers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
import time
import requests
from bs4 import BeautifulSoup
from utils.logger import get_logger
from utils.decorators import retry_on_exception
from config.constants import API_RETRY_COUNT, API_RETRY_DELAY

logger = get_logger("wholesaler_base")


@dataclass
class RawProduct:
    """Scraped product data before database storage."""
    name: str
    wholesale_price: float
    image_url: str
    description: str = ""
    category: str = ""
    moq: int = 1
    external_product_id: str = ""
    wholesaler_name: str = ""


class BaseWholesalerClient(ABC):
    """Abstract base class for wholesaler scrapers."""

    wholesaler_name: str = ""
    base_url: str = ""
    login_url: str = ""

    def __init__(self, username: str = "", password: str = ""):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
            }
        )
        self._logged_in = False
        self.logger = get_logger(f"wholesaler_{self.wholesaler_name}")

    # ── Authentication ────────────────────────────────────────────────────────

    def login(self) -> bool:
        """Log in to the wholesaler site.  Returns True on success."""
        if not self.username or not self.password:
            self.logger.warning(f"[{self.wholesaler_name}] No credentials provided, skipping login.")
            return False
        try:
            result = self._do_login()
            self._logged_in = result
            if result:
                self.logger.info(f"[{self.wholesaler_name}] Logged in successfully.")
            else:
                self.logger.warning(f"[{self.wholesaler_name}] Login failed.")
            return result
        except Exception as exc:
            self.logger.error(f"[{self.wholesaler_name}] Login exception: {exc}")
            return False

    def _do_login(self) -> bool:
        """Override in subclass to implement actual login logic."""
        return False

    # ── Scraping ──────────────────────────────────────────────────────────────

    @retry_on_exception(retries=API_RETRY_COUNT, delay=API_RETRY_DELAY)
    def scrape_products(self, max_products: int = 200) -> List[RawProduct]:
        """Scrape up to *max_products* products from the wholesaler site."""
        if not self._logged_in:
            self.login()
        return self._scrape_products(max_products)

    @abstractmethod
    def _scrape_products(self, max_products: int) -> List[RawProduct]:
        """Implement actual scraping in subclasses."""
        ...

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_soup(self, url: str, params: dict = None) -> Optional[BeautifulSoup]:
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as exc:
            self.logger.error(f"[{self.wholesaler_name}] GET {url} failed: {exc}")
            return None

    def _parse_price(self, text: str) -> Optional[float]:
        import re
        if not text:
            return None
        cleaned = re.sub(r"[^\d.]", "", text.strip())
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _sleep(self, seconds: float = 1.0):
        time.sleep(seconds)
