import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CashFlowMonitor:
    """Tracks and monitors business cash flow."""

    def __init__(self, db_session=None):
        self.db = db_session

    def get_current_balance(self) -> int:
        """Return the current closing cash balance for today."""
        if not self.db:
            return 0
        from database.crud import get_or_create_cash_flow
        cf = get_or_create_cash_flow(self.db, date.today())
        return cf.closing_balance

    def record_income(
        self, amount: int, description: str, order_id: Optional[int] = None
    ) -> Dict:
        """Record an income transaction and update today's cash flow."""
        logger.info(f"Recording income: {amount:,}원 - {description}")
        if self.db:
            from database.crud import create_transaction, update_cash_flow, get_or_create_cash_flow
            from database.schemas import TransactionCreate
            get_or_create_cash_flow(self.db, date.today())
            tx = create_transaction(
                self.db,
                TransactionCreate(
                    order_id=order_id,
                    type="income",
                    amount=amount,
                    description=description,
                    category="sales",
                ),
            )
            update_cash_flow(self.db, date.today(), income=amount)
            return {"id": tx.id, "amount": amount, "type": "income"}
        return {"amount": amount, "type": "income", "description": description}

    def record_expense(
        self, amount: int, description: str, category: str = "purchase"
    ) -> Dict:
        """Record an expense transaction and update today's cash flow."""
        logger.info(f"Recording expense: {amount:,}원 - {description} [{category}]")
        if self.db:
            from database.crud import create_transaction, update_cash_flow, get_or_create_cash_flow
            from database.schemas import TransactionCreate
            get_or_create_cash_flow(self.db, date.today())
            tx = create_transaction(
                self.db,
                TransactionCreate(
                    type="expense",
                    amount=amount,
                    description=description,
                    category=category,
                ),
            )
            update_cash_flow(self.db, date.today(), expense=amount)
            return {"id": tx.id, "amount": amount, "type": "expense"}
        return {"amount": amount, "type": "expense", "description": description}

    def check_budget_status(self) -> Dict:
        """Return today's budget utilization."""
        if not self.db:
            return {"daily_budget": 500000, "spent": 0, "remaining": 500000, "percent_used": 0.0}
        from database.crud import get_budget_status, create_or_get_budget
        today = date.today()
        budget = create_or_get_budget(self.db, today)
        pct = (budget.spent_amount / max(budget.daily_budget, 1)) * 100
        return {
            "date": today.isoformat(),
            "daily_budget": budget.daily_budget,
            "spent": budget.spent_amount,
            "remaining": budget.remaining,
            "percent_used": round(pct, 2),
            "is_over_budget": budget.spent_amount > budget.daily_budget,
        }

    def get_daily_summary(self, target_date: Optional[date] = None) -> Dict:
        """Return income/expense summary for a specific date."""
        target_date = target_date or date.today()
        if not self.db:
            return {"date": target_date.isoformat(), "income": 0, "expense": 0, "net": 0}
        from database.crud import get_or_create_cash_flow
        cf = get_or_create_cash_flow(self.db, target_date)
        return {
            "date": target_date.isoformat(),
            "income": cf.total_income,
            "expense": cf.total_expense,
            "net": cf.net_flow,
            "opening_balance": cf.opening_balance,
            "closing_balance": cf.closing_balance,
        }

    def get_weekly_report(self) -> Dict:
        """Return aggregated report for the past 7 days."""
        end = date.today()
        start = end - timedelta(days=6)
        daily_summaries = []
        total_income = 0
        total_expense = 0
        current = start
        while current <= end:
            summary = self.get_daily_summary(current)
            daily_summaries.append(summary)
            total_income += summary["income"]
            total_expense += summary["expense"]
            current += timedelta(days=1)
        return {
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "total_income": total_income,
            "total_expense": total_expense,
            "net_profit": total_income - total_expense,
            "daily_average_income": total_income // 7,
            "daily_average_expense": total_expense // 7,
            "daily_summaries": daily_summaries,
        }

    def check_cash_warning(self) -> bool:
        """Send Telegram warning if cash balance is below threshold. Returns True if warning sent."""
        current = self.get_current_balance()
        threshold = 100000
        try:
            from config.settings import get_settings
            settings = get_settings()
            threshold = settings.cash_warning_threshold
        except Exception:
            pass

        if current < threshold:
            logger.warning(f"Cash balance {current:,}원 below threshold {threshold:,}원")
            try:
                from config.settings import get_settings
                settings = get_settings()
                if settings.telegram_bot_token:
                    import asyncio
                    from integrations.telegram_bot import TelegramBot
                    bot = TelegramBot(settings.telegram_bot_token, settings.telegram_chat_id)
                    asyncio.get_event_loop().run_until_complete(bot.send_cash_warning(current))
                    return True
            except Exception as exc:
                logger.error(f"Failed to send cash warning: {exc}")
        return False

    def project_monthly_cash_flow(self) -> Dict:
        """Project end-of-month balance based on current trend."""
        today = date.today()
        days_passed = today.day
        weekly = self.get_weekly_report()
        daily_avg_income = weekly["total_income"] / 7 if weekly["total_income"] else 0
        daily_avg_expense = weekly["total_expense"] / 7 if weekly["total_expense"] else 0
        days_remaining = 30 - days_passed
        projected_income = daily_avg_income * days_remaining
        projected_expense = daily_avg_expense * days_remaining
        current_balance = self.get_current_balance()
        projected_balance = current_balance + projected_income - projected_expense
        return {
            "current_date": today.isoformat(),
            "current_balance": current_balance,
            "days_remaining_in_month": days_remaining,
            "projected_additional_income": int(projected_income),
            "projected_additional_expense": int(projected_expense),
            "projected_end_balance": int(projected_balance),
            "daily_avg_income": int(daily_avg_income),
            "daily_avg_expense": int(daily_avg_expense),
        }
