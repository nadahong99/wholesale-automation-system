# utils/helpers.py
import time
import math
import re
from typing import Any, Callable, TypeVar, Optional
from functools import wraps
from utils.logger import get_logger

logger = get_logger("helpers")
T = TypeVar("T")


def retry(func: Callable, retries: int = 3, delay: float = 2.0, exceptions=(Exception,)):
    """Retry a callable up to *retries* times with *delay* seconds between attempts."""
    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            return func()
        except exceptions as exc:
            last_exc = exc
            logger.warning(f"Attempt {attempt}/{retries} failed: {exc}")
            if attempt < retries:
                time.sleep(delay)
    raise last_exc  # type: ignore[misc]


def format_price(price: float) -> int:
    """Round price to the nearest won (Korean currency unit)."""
    return int(round(price))


def calculate_margin(wholesale_price: float, selling_price: float) -> float:
    """Return margin as a percentage."""
    if selling_price <= 0:
        return 0.0
    return ((selling_price - wholesale_price) / selling_price) * 100.0


def calculate_selling_price(wholesale_price: float, margin_percent: float = 20.0) -> int:
    """Calculate the minimum selling price to achieve *margin_percent*."""
    if margin_percent >= 100:
        raise ValueError("Margin percent must be less than 100")
    selling_price = wholesale_price / (1 - margin_percent / 100.0)
    return format_price(selling_price)


def clean_price_string(price_str: str) -> Optional[float]:
    """Convert a Korean price string like '12,500원' to a float."""
    if not price_str:
        return None
    cleaned = re.sub(r"[^\d.]", "", price_str)
    try:
        return float(cleaned)
    except ValueError:
        return None


def chunk_list(lst: list, size: int) -> list:
    """Split *lst* into chunks of *size*."""
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Division that returns *default* when denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def truncate_string(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_korean_number(n: int) -> str:
    """Format a number with Korean comma separator and 원 suffix."""
    return f"{n:,}원"
