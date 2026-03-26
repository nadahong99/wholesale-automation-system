import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

PLATFORM_FEE_RATES: Dict[str, float] = {
    "naver": 0.055,
    "coupang": 0.108,
}
DEFAULT_SHIPPING_COST = 3000


class MarginCalculator:
    """Calculates product margins accounting for platform fees and shipping."""

    def __init__(
        self,
        naver_fee: float = 0.055,
        coupang_fee: float = 0.108,
        shipping_cost: int = DEFAULT_SHIPPING_COST,
    ):
        self.fee_rates = {"naver": naver_fee, "coupang": coupang_fee}
        self.shipping_cost = shipping_cost

    def _get_fee_rate(self, platform: str) -> float:
        return self.fee_rates.get(platform.lower(), 0.055)

    def calculate_margin(
        self, purchase_price: int, selling_price: int, platform: str = "naver"
    ) -> float:
        """
        margin = (selling_price - purchase_price - platform_fee - shipping) / selling_price
        Returns margin as a percentage (0-100).
        """
        if selling_price <= 0:
            return 0.0
        fee_rate = self._get_fee_rate(platform)
        platform_fee = selling_price * fee_rate
        total_cost = purchase_price + platform_fee + self.shipping_cost
        profit = selling_price - total_cost
        margin_pct = (profit / selling_price) * 100
        logger.debug(
            f"Margin calc: purchase={purchase_price} sell={selling_price} "
            f"platform={platform} fee={platform_fee:.0f} margin={margin_pct:.2f}%"
        )
        return round(margin_pct, 2)

    def validate_minimum_margin(
        self, margin: float, min_percent: float = 20.0
    ) -> bool:
        """Return True if margin meets the minimum threshold."""
        return margin >= min_percent

    def suggest_selling_price(
        self,
        purchase_price: int,
        platform: str = "naver",
        target_margin: float = 0.25,
    ) -> int:
        """
        Solve: target_margin = (sp - purchase - sp*fee - shipping) / sp
        => sp * (1 - fee - target_margin) = purchase + shipping
        => sp = (purchase + shipping) / (1 - fee - target_margin)
        """
        fee_rate = self._get_fee_rate(platform)
        denominator = 1 - fee_rate - target_margin
        if denominator <= 0:
            raise ValueError(
                f"Cannot achieve {target_margin*100:.1f}% margin on {platform}: "
                "fee_rate too high"
            )
        raw_price = (purchase_price + self.shipping_cost) / denominator
        # Round up to nearest 100 won
        return int((raw_price // 100 + 1) * 100)

    def calculate_bundle_price(
        self, unit_price: int, quantity: int, platform: str = "naver"
    ) -> Dict[str, int]:
        """Calculate bundle pricing with a 5% discount for quantity >= 5."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        discount = 0.05 if quantity >= 5 else 0.0
        bundle_unit_price = int(unit_price * (1 - discount))
        total_price = bundle_unit_price * quantity
        return {
            "unit_price": bundle_unit_price,
            "quantity": quantity,
            "total_price": total_price,
            "discount_percent": int(discount * 100),
        }

    def get_fee_breakdown(
        self, purchase_price: int, selling_price: int, platform: str = "naver"
    ) -> Dict[str, float]:
        """Return detailed cost breakdown for a product."""
        fee_rate = self._get_fee_rate(platform)
        platform_fee = selling_price * fee_rate
        total_cost = purchase_price + platform_fee + self.shipping_cost
        profit = selling_price - total_cost
        margin_pct = self.calculate_margin(purchase_price, selling_price, platform)
        return {
            "purchase_price": purchase_price,
            "selling_price": selling_price,
            "platform_fee": round(platform_fee, 2),
            "platform_fee_rate": fee_rate,
            "shipping_cost": self.shipping_cost,
            "total_cost": round(total_cost, 2),
            "profit": round(profit, 2),
            "margin_percent": margin_pct,
            "meets_minimum": self.validate_minimum_margin(margin_pct),
        }

    def calculate_net_profit(
        self, purchase_price: int, selling_price: int, platform: str = "naver", quantity: int = 1
    ) -> int:
        """Calculate total net profit for a given quantity sold."""
        breakdown = self.get_fee_breakdown(purchase_price, selling_price, platform)
        return int(breakdown["profit"] * quantity)
