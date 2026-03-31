import logging
from datetime import datetime
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Inventory, PriceHistory, Order

logger = logging.getLogger(__name__)

LOW_STOCK_THRESHOLD = 10


def check_low_stock():
    """Detect low-stock products and emit warning logs."""
    db: Session = SessionLocal()
    try:
        low_stock_items = (
            db.query(Inventory)
            .filter(Inventory.stock_quantity < LOW_STOCK_THRESHOLD)
            .all()
        )
        if low_stock_items:
            for item in low_stock_items:
                logger.warning(
                    "[Low Stock Alert] product_id=%s stock=%s (threshold=%s)",
                    item.product_id,
                    item.stock_quantity,
                    LOW_STOCK_THRESHOLD,
                )
        else:
            logger.info("[Inventory Check] No low-stock products found.")
    finally:
        db.close()


def check_price_changes():
    """Detect price records added today and emit info logs."""
    db: Session = SessionLocal()
    try:
        today = str(datetime.utcnow().date())
        recent_prices = (
            db.query(PriceHistory)
            .filter(PriceHistory.date_recorded == today)
            .all()
        )
        if recent_prices:
            for record in recent_prices:
                logger.info(
                    "[Price Change] product_id=%s price=%s date=%s",
                    record.product_id,
                    record.price,
                    record.date_recorded,
                )
        else:
            logger.info("[Price Check] No price changes recorded today.")
    finally:
        db.close()


def generate_daily_order_summary():
    """Log a daily summary of orders placed today."""
    db: Session = SessionLocal()
    try:
        today = str(datetime.utcnow().date())
        orders_today = (
            db.query(Order)
            .filter(Order.order_date == today)
            .all()
        )
        total_quantity = sum(o.quantity for o in orders_today)
        logger.info(
            "[Daily Order Summary] date=%s orders=%s total_quantity=%s",
            today,
            len(orders_today),
            total_quantity,
        )
    finally:
        db.close()
