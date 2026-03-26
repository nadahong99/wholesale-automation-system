# monitoring/cash_flow_monitor.py
"""Cash flow tracking and low-cash alerts."""
from datetime import datetime, date
from typing import Dict
from database.session import SessionLocal
from database import crud, models
from integrations.telegram_bot import send_message
from config.constants import CASH_WARNING_THRESHOLD
from utils.logger import get_logger

logger = get_logger("cash_flow_monitor")


def get_cash_flow_summary(db) -> Dict:
    """Return today's cash flow metrics."""
    report = crud.get_or_create_daily_report(db, datetime.utcnow().date())
    budget = crud.get_or_create_budget(db)
    return {
        "date": str(report.date),
        "total_sales": report.total_sales,
        "total_cost": report.total_cost,
        "total_profit": report.total_profit,
        "margin_percent": report.margin_percent,
        "cash_available": budget.remaining,
        "daily_budget": budget.daily_budget,
        "budget_spent": budget.spent,
    }


def check_and_alert(db) -> bool:
    """Send Telegram alert if available cash drops below threshold."""
    summary = get_cash_flow_summary(db)
    cash = summary["cash_available"]
    if cash < CASH_WARNING_THRESHOLD:
        msg = (
            f"⚠️ <b>현금 부족 경고!</b>\n\n"
            f"현재 잔액: {int(cash):,}원\n"
            f"경고 기준: {CASH_WARNING_THRESHOLD:,}원\n"
            f"즉시 예산을 보충해 주세요!"
        )
        send_message(msg)
        logger.warning(f"Low cash alert sent: {int(cash):,}원 remaining.")
        return True
    return False


def run_cash_flow_check() -> Dict:
    db = SessionLocal()
    try:
        summary = get_cash_flow_summary(db)
        check_and_alert(db)
        return summary
    finally:
        db.close()
