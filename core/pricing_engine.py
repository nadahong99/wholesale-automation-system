import logging
import random
from datetime import datetime
from typing import Dict, List, Optional

from core.margin_calculator import MarginCalculator

logger = logging.getLogger(__name__)


class PricingEngine:
    """Determines optimal pricing by analysing competitor prices."""

    def __init__(self):
        self.margin_calc = MarginCalculator()
        self._price_history: Dict[int, List[Dict]] = {}

    def get_competitor_prices(self, product_name: str) -> List[int]:
        """Fetch competitor prices for a product (mock implementation)."""
        base_keyword_hash = abs(hash(product_name)) % 50000 + 10000
        prices = []
        for i in range(5):
            variation = random.randint(-3000, 5000)
            prices.append(base_keyword_hash + variation)
        logger.info(f"Fetched {len(prices)} competitor prices for '{product_name}'")
        return sorted(prices)

    def calculate_optimal_price(
        self,
        purchase_price: int,
        competitor_prices: List[int],
        platform: str = "naver",
        target_margin: float = 0.25,
    ) -> int:
        """
        Recommend a price that is competitive (within 5% of median)
        while meeting the target margin.
        """
        if not competitor_prices:
            return self.margin_calc.suggest_selling_price(purchase_price, platform, target_margin)

        sorted_prices = sorted(competitor_prices)
        median_idx = len(sorted_prices) // 2
        median_price = sorted_prices[median_idx]

        min_viable = self.margin_calc.suggest_selling_price(purchase_price, platform, target_margin)
        # Try to price 2% below median but not below min viable price
        target_price = int(median_price * 0.98)
        if target_price < min_viable:
            target_price = min_viable

        # Round to nearest 100
        optimal = int((target_price // 100) * 100)
        logger.info(
            f"Optimal price for platform={platform}: median={median_price} "
            f"min_viable={min_viable} recommended={optimal}"
        )
        return optimal

    def is_price_competitive(
        self, our_price: int, competitor_prices: List[int], threshold: float = 0.10
    ) -> bool:
        """Return True if our price is within threshold of the lowest competitor price."""
        if not competitor_prices:
            return True
        min_competitor = min(competitor_prices)
        return our_price <= min_competitor * (1 + threshold)

    def get_price_recommendation(
        self, product_name: str, purchase_price: int, platform: str = "naver"
    ) -> Dict:
        """Full price recommendation including competitor analysis."""
        competitor_prices = self.get_competitor_prices(product_name)
        optimal_price = self.calculate_optimal_price(purchase_price, competitor_prices, platform)
        margin = self.margin_calc.calculate_margin(purchase_price, optimal_price, platform)
        is_competitive = self.is_price_competitive(optimal_price, competitor_prices)
        breakdown = self.margin_calc.get_fee_breakdown(purchase_price, optimal_price, platform)
        return {
            "product_name": product_name,
            "purchase_price": purchase_price,
            "recommended_price": optimal_price,
            "platform": platform,
            "margin_percent": margin,
            "is_competitive": is_competitive,
            "competitor_prices": competitor_prices,
            "min_competitor_price": min(competitor_prices) if competitor_prices else None,
            "max_competitor_price": max(competitor_prices) if competitor_prices else None,
            "fee_breakdown": breakdown,
        }

    def monitor_price_changes(
        self, product_id: int, current_price: int
    ) -> Optional[Dict]:
        """Record a price observation and return change info if price changed."""
        history = self._price_history.setdefault(product_id, [])
        record = {"price": current_price, "timestamp": datetime.utcnow().isoformat()}

        if history:
            last_price = history[-1]["price"]
            history.append(record)
            if last_price != current_price:
                change_pct = (current_price - last_price) / last_price * 100
                logger.info(
                    f"Price change detected for product {product_id}: "
                    f"{last_price} -> {current_price} ({change_pct:+.1f}%)"
                )
                return {
                    "product_id": product_id,
                    "old_price": last_price,
                    "new_price": current_price,
                    "change_amount": current_price - last_price,
                    "change_percent": round(change_pct, 2),
                }
        else:
            history.append(record)
        return None

    def get_price_history(self, product_id: int) -> List[Dict]:
        """Return price history for a product."""
        return self._price_history.get(product_id, [])
