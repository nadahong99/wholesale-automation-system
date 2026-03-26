import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PriceMonitor:
    """Monitors product prices and detects significant changes."""

    def __init__(self, db_session=None, threshold: float = 0.05):
        self.db = db_session
        self.threshold = threshold
        self._alerts: List[Dict] = []

    def monitor_all_products(self) -> List[Dict]:
        """Check prices for all listed products and return change alerts."""
        if not self.db:
            logger.warning("PriceMonitor: no DB session")
            return []
        from database.models import Product
        products = (
            self.db.query(Product)
            .filter(Product.status.in_(["LISTED", "APPROVED"]))
            .all()
        )
        changes = []
        for product in products:
            alert = self.check_product_price(product.id)
            if alert:
                changes.append(alert)
        logger.info(f"PriceMonitor: checked {len(products)} products, {len(changes)} changes")
        return changes

    def check_product_price(self, product_id: int) -> Optional[Dict]:
        """Check a single product's current price vs stored price."""
        if not self.db:
            return None
        from database.models import Product
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None
        # Simulate fetching current market price
        import random
        variation = random.uniform(-0.08, 0.06)
        current_market_price = int(product.selling_price * (1 + variation))
        return self.generate_price_alert(
            {
                "id": product.id,
                "name": product.name,
                "platform": product.platform,
            },
            product.selling_price,
            current_market_price,
        )

    def detect_price_changes(
        self, old_price: int, new_price: int, threshold: float = 0.05
    ) -> bool:
        """Return True if price changed by more than threshold."""
        if old_price == 0:
            return new_price != 0
        change = abs(new_price - old_price) / old_price
        return change >= threshold

    def generate_price_alert(
        self, product: Dict, old_price: int, new_price: int
    ) -> Optional[Dict]:
        """Create an alert dict if price changed significantly."""
        if not self.detect_price_changes(old_price, new_price, self.threshold):
            return None
        change_pct = (new_price - old_price) / max(old_price, 1) * 100
        alert = {
            "product_id": product.get("id"),
            "product_name": product.get("name"),
            "platform": product.get("platform"),
            "old_price": old_price,
            "new_price": new_price,
            "change_amount": new_price - old_price,
            "change_percent": round(change_pct, 2),
            "alert_type": "price_drop" if new_price < old_price else "price_increase",
            "detected_at": datetime.utcnow().isoformat(),
        }
        self._alerts.append(alert)
        logger.info(
            f"Price alert: {product.get('name')} {old_price} -> {new_price} "
            f"({change_pct:+.1f}%)"
        )
        return alert

    def get_price_history(self, product_id: int, days: int = 30) -> List[Dict]:
        """Return simulated price history for a product."""
        if not self.db:
            return []
        from database.models import Product
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return []
        import random
        history = []
        current_date = date.today() - timedelta(days=days)
        price = product.selling_price
        while current_date <= date.today():
            history.append({
                "date": current_date.isoformat(),
                "price": price,
                "product_id": product_id,
            })
            price = int(price * random.uniform(0.97, 1.03))
            current_date += timedelta(days=1)
        return history

    def send_alerts_for_changes(self, changes: List[Dict]) -> int:
        """Send Telegram notifications for price changes, return count sent."""
        if not changes:
            return 0
        import asyncio
        try:
            from config.settings import get_settings
            settings = get_settings()
            if not settings.telegram_bot_token:
                logger.debug(f"[Mock] Would send {len(changes)} price alerts")
                return 0
            from integrations.telegram_bot import TelegramBot
            bot = TelegramBot(settings.telegram_bot_token, settings.telegram_chat_id)
            for change in changes:
                text = (
                    f"💰 <b>가격 변동 알림</b>\n"
                    f"상품: {change['product_name']}\n"
                    f"이전: {change['old_price']:,}원 → 현재: {change['new_price']:,}원\n"
                    f"변동: {change['change_percent']:+.1f}%"
                )
                asyncio.get_event_loop().run_until_complete(bot.send_message(text))
            return len(changes)
        except Exception as exc:
            logger.error(f"Failed to send price alerts: {exc}")
            return 0

    def get_pending_alerts(self) -> List[Dict]:
        """Return all pending alerts collected since last clear."""
        return list(self._alerts)

    def clear_alerts(self) -> None:
        """Clear the internal alert buffer."""
        self._alerts.clear()
