# core/margin_calculator.py
"""Margin and golden-keyword filtering logic."""
from typing import Dict, List, Optional, Tuple
from utils.logger import get_logger
from utils.helpers import calculate_margin, calculate_selling_price, safe_divide
from config.constants import GOLDEN_KEYWORD_THRESHOLD, MIN_MARGIN_PERCENT
from config.settings import settings

logger = get_logger("margin_calculator")


class MarginCalculator:
    """Compute selling prices and validate margins."""

    def __init__(self, min_margin_percent: float = None):
        self.min_margin = min_margin_percent or settings.MIN_MARGIN_PERCENT

    def compute_selling_price(self, wholesale_price: float) -> int:
        """Return the minimum selling price that satisfies *self.min_margin*."""
        return calculate_selling_price(wholesale_price, self.min_margin)

    def compute_margin(self, wholesale_price: float, selling_price: float) -> float:
        return calculate_margin(wholesale_price, selling_price)

    def is_margin_ok(self, wholesale_price: float, selling_price: float) -> bool:
        return self.compute_margin(wholesale_price, selling_price) >= self.min_margin

    def adjust_price_for_competitor(
        self,
        wholesale_price: float,
        competitor_price: float,
        target_margin: float = None,
    ) -> Optional[int]:
        """
        Return a competitive price that stays above *min_margin*.
        If beating the competitor makes margin drop below minimum, return None.
        """
        target_margin = target_margin or self.min_margin
        # Try to beat competitor by 1%
        desired_price = int(competitor_price * 0.99)
        margin = self.compute_margin(wholesale_price, desired_price)
        if margin >= self.min_margin:
            return desired_price
        # Fall back to minimum viable price (list at our minimum, cannot beat competitor)
        min_price = self.compute_selling_price(wholesale_price)
        return min_price


class GoldenKeywordFilter:
    """Filter products using the Naver golden-keyword criterion."""

    def __init__(self, threshold: float = None):
        self.threshold = threshold or settings.GOLDEN_KEYWORD_THRESHOLD

    def calculate_score(self, search_volume: int, product_count: int) -> float:
        """golden_keyword_score = search_volume / max(product_count, 1)."""
        return safe_divide(float(search_volume), max(product_count, 1))

    def is_golden(self, search_volume: int, product_count: int) -> bool:
        return self.calculate_score(search_volume, product_count) >= self.threshold

    def filter_products(
        self,
        products: List[Dict],
        min_results: int = 50,
        max_results: int = 100,
    ) -> List[Dict]:
        """
        *products* must be a list of dicts with 'search_volume' and
        'product_count_in_market' keys.  Returns scored & filtered subset.
        """
        scored = []
        for p in products:
            sv = p.get("search_volume", 0)
            pc = p.get("product_count_in_market", 1)
            score = self.calculate_score(sv, pc)
            if score >= self.threshold:
                scored.append({**p, "golden_keyword_score": score})

        # Sort by score descending
        scored.sort(key=lambda x: x["golden_keyword_score"], reverse=True)

        if len(scored) < min_results:
            logger.warning(
                f"Only {len(scored)} golden-keyword products found (min={min_results})."
            )

        return scored[:max_results]
