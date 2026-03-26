# core/pricing_engine.py
"""Real-time competitive pricing engine."""
from typing import Optional, List
from sqlalchemy.orm import Session
from database import crud, models
from database.schemas import ProductUpdate
from core.margin_calculator import MarginCalculator
from integrations.naver_api import NaverShoppingClient
from integrations.coupang_api import CoupangClient
from utils.logger import get_logger
from utils.helpers import calculate_margin

logger = get_logger("pricing_engine")


class PricingEngine:
    def __init__(self):
        self.calc = MarginCalculator()
        self.naver = NaverShoppingClient()
        self.coupang = CoupangClient()

    def get_competitor_prices(self, product_name: str) -> List[float]:
        """Gather competitor prices from Naver Shopping."""
        return self.naver.get_competitor_prices(product_name, top_n=5)

    def compute_optimal_price(
        self,
        product: models.Product,
        competitor_prices: List[float],
    ) -> Optional[int]:
        """
        Return the best competitive price that maintains minimum margin.
        If no profitable price exists, return the minimum viable price.
        """
        min_price = self.calc.compute_selling_price(product.wholesale_price)

        if not competitor_prices:
            return min_price

        lowest_competitor = min(competitor_prices)
        adjusted = self.calc.adjust_price_for_competitor(
            product.wholesale_price, lowest_competitor
        )
        if adjusted is not None:
            return adjusted

        # Cannot beat competitor profitably; return minimum viable
        return min_price

    def update_product_price(self, db: Session, product: models.Product, new_price: int) -> bool:
        """Persist new price to DB and push to Naver/Coupang."""
        try:
            crud.update_product(
                db,
                product.id,
                ProductUpdate(actual_selling_price=float(new_price)),
            )

            margin = calculate_margin(product.wholesale_price, new_price)
            crud.add_price_history(
                db,
                product_id=product.id,
                competitor_price=0.0,
                our_price=float(new_price),
                margin_percent=margin,
                platform="system",
            )

            # Push to Coupang if listed
            if product.coupang_product_id:
                ok = self.coupang.update_price(product.coupang_product_id, new_price)
                if not ok:
                    logger.warning(f"Coupang price update failed for product {product.id}")

            return True
        except Exception as exc:
            logger.error(f"update_product_price failed for product {product.id}: {exc}")
            return False

    def run_price_adjustment(self, db: Session) -> int:
        """
        Iterate over all listed products, check competitor prices,
        and adjust if needed. Returns number of products adjusted.
        """
        products = crud.get_listed_products(db)
        adjusted = 0

        for product in products:
            try:
                competitor_prices = self.get_competitor_prices(product.name)
                if not competitor_prices:
                    continue

                optimal = self.compute_optimal_price(product, competitor_prices)
                current = product.actual_selling_price or product.suggested_selling_price

                if optimal and optimal != int(current or 0):
                    ok = self.update_product_price(db, product, optimal)
                    if ok:
                        adjusted += 1
                        logger.info(
                            f"Price adjusted for '{product.name}': {int(current or 0):,} → {optimal:,}원"
                        )

                # Record competitor price in history
                if competitor_prices:
                    margin = calculate_margin(product.wholesale_price, current or 0)
                    crud.add_price_history(
                        db,
                        product_id=product.id,
                        competitor_price=min(competitor_prices),
                        our_price=float(current or 0),
                        margin_percent=margin,
                        platform="naver",
                    )
            except Exception as exc:
                logger.error(f"Price adjustment failed for product {product.id}: {exc}")

        logger.info(f"Price adjustment complete. {adjusted} products updated.")
        return adjusted
