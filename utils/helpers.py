import re
import time
import math
import unicodedata
from typing import Any, Callable, List, Optional, TypeVar
from urllib.parse import urlparse

T = TypeVar("T")


def format_korean_won(amount: float) -> str:
    """Format an integer amount as Korean Won string."""
    return f"{int(amount):,}원"


def calculate_percentage(part: float, total: float) -> float:
    """Return part/total as a percentage, or 0 if total is zero."""
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)


def truncate_string(s: str, max_len: int, suffix: str = "...") -> str:
    """Truncate a string to max_len characters, appending suffix if truncated."""
    if len(s) <= max_len:
        return s
    return s[: max_len - len(suffix)] + suffix


def sanitize_filename(name: str) -> str:
    """Remove or replace characters not safe for filenames."""
    name = unicodedata.normalize("NFC", name)
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = name.strip(". ")
    return name or "unnamed"


def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """Call func, retrying up to max_retries times with exponential backoff."""
    last_exc: Exception = RuntimeError("No attempts made")
    for attempt in range(max_retries):
        try:
            return func()
        except exceptions as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                sleep_time = delay * (2 ** attempt)
                time.sleep(sleep_time)
    raise last_exc


def chunk_list(lst: List[T], size: int) -> List[List[T]]:
    """Split a list into chunks of the given size."""
    if size <= 0:
        raise ValueError("Chunk size must be positive")
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def is_valid_url(url: str) -> bool:
    """Return True if url is a valid http/https URL."""
    try:
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False


def parse_price_string(price_str: str) -> int:
    """Parse Korean price strings like '12,000원' or '₩12000' to int."""
    if not price_str:
        return 0
    cleaned = re.sub(r"[^\d]", "", str(price_str))
    return int(cleaned) if cleaned else 0


def extract_numbers(text: str) -> List[float]:
    """Extract all numbers (including decimals) from a string."""
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]


def calculate_moving_average(data: List[float], window: int) -> List[float]:
    """Calculate simple moving average with the given window size."""
    if window <= 0:
        raise ValueError("Window must be positive")
    result: List[float] = []
    for i in range(len(data)):
        start = max(0, i - window + 1)
        subset = data[start : i + 1]
        result.append(round(sum(subset) / len(subset), 4))
    return result


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min_val and max_val."""
    return max(min_val, min(max_val, value))


def round_to_nearest(value: float, nearest: int = 100) -> int:
    """Round value to the nearest multiple (e.g. 100 for Korean pricing)."""
    return int(round(value / nearest) * nearest)
