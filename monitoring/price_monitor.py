# monitoring/price_monitor.py
"""Hourly competitor price monitoring and auto-adjustment."""
from datetime import datetime
from sqlalchemy.orm import Session
from database.session import SessionLocal
from database import crud
from core.pricing_engine import PricingEngine
from utils.logger import get_logger
from utils.decorators import log_execution_time

logger = get_logger("price_monitor")


@log_execution_time
def run_price_monitoring() -> int:
    """
    Check competitor prices for all listed products and auto-adjust.
    Returns number of products whose price was updated.
    """
    db = SessionLocal()
    try:
        engine = PricingEngine()
        adjusted = engine.run_price_adjustment(db)
        logger.info(f"Price monitoring run complete: {adjusted} products adjusted.")
        return adjusted
    except Exception as exc:
        logger.error(f"run_price_monitoring error: {exc}")
        return 0
    finally:
        db.close()
