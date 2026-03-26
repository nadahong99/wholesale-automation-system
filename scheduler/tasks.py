import logging
from datetime import date, datetime

from scheduler.celery_app import app

logger = logging.getLogger(__name__)


def _get_db():
    from database.session import get_session_factory
    return get_session_factory()()


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_morning_sourcing(self):
    """6:00 AM - Morning sourcing run."""
    logger.info("Task: run_morning_sourcing started")
    db = None
    try:
        db = _get_db()
        from core.sourcing_engine import SourcingEngine
        engine = SourcingEngine(db_session=db)
        result = engine.run_full_sourcing()
        logger.info(
            f"Morning sourcing done: scraped={result.total_scraped} "
            f"actionable={result.total_actionable}"
        )
        return {
            "status": "success",
            "total_scraped": result.total_scraped,
            "total_actionable": result.total_actionable,
        }
    except Exception as exc:
        logger.error(f"run_morning_sourcing failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        if db:
            db.close()


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_afternoon_sourcing(self):
    """14:00 - Afternoon sourcing run."""
    logger.info("Task: run_afternoon_sourcing started")
    db = None
    try:
        db = _get_db()
        from core.sourcing_engine import SourcingEngine
        engine = SourcingEngine(db_session=db)
        result = engine.run_full_sourcing()
        logger.info(
            f"Afternoon sourcing done: scraped={result.total_scraped} "
            f"actionable={result.total_actionable}"
        )
        return {
            "status": "success",
            "total_scraped": result.total_scraped,
            "total_actionable": result.total_actionable,
        }
    except Exception as exc:
        logger.error(f"run_afternoon_sourcing failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        if db:
            db.close()


@app.task(bind=True, max_retries=2, default_retry_delay=30)
def run_price_monitor(self):
    """9:00 and 16:00 - Price monitoring run."""
    logger.info("Task: run_price_monitor started")
    db = None
    try:
        db = _get_db()
        from monitoring.price_monitor import PriceMonitor
        monitor = PriceMonitor(db_session=db)
        changes = monitor.monitor_all_products()
        if changes:
            monitor.send_alerts_for_changes(changes)
        logger.info(f"Price monitor done: {len(changes)} changes detected")
        return {"status": "success", "changes_detected": len(changes)}
    except Exception as exc:
        logger.error(f"run_price_monitor failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        if db:
            db.close()


@app.task(bind=True, max_retries=2, default_retry_delay=60)
def send_daily_report(self):
    """20:00 - Send daily performance report via Telegram."""
    logger.info("Task: send_daily_report started")
    db = None
    try:
        db = _get_db()
        from monitoring.performance_tracker import PerformanceTracker
        from monitoring.cash_flow_monitor import CashFlowMonitor
        tracker = PerformanceTracker(db)
        cash_monitor = CashFlowMonitor(db)
        report = tracker.generate_performance_report("daily")
        summary = cash_monitor.get_daily_summary(date.today())
        from config.settings import get_settings
        settings = get_settings()
        if settings.telegram_bot_token:
            import asyncio
            from integrations.telegram_bot import TelegramBot
            bot = TelegramBot(settings.telegram_bot_token, settings.telegram_chat_id)
            report_data = {
                "date": date.today().isoformat(),
                "total_revenue": summary["income"],
                "order_count": report.get("roi", {}).get("total_revenue", 0),
                "net_profit": summary["net"],
                "margin_percent": report.get("roi", {}).get("roi_percent", 0),
                "sourced_products": 0,
            }
            asyncio.get_event_loop().run_until_complete(bot.send_daily_report(report_data))
        logger.info("Daily report sent")
        return {"status": "success", "report_date": date.today().isoformat()}
    except Exception as exc:
        logger.error(f"send_daily_report failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        if db:
            db.close()


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def check_pending_orders(self):
    """Every 30 min - Poll and process pending orders."""
    logger.info("Task: check_pending_orders started")
    db = None
    try:
        db = _get_db()
        from core.order_processor import OrderProcessor
        processor = OrderProcessor(db_session=db)
        new_orders = processor.poll_new_orders()
        processed = 0
        for order in new_orders:
            try:
                processor.process_order(order)
                processed += 1
            except Exception as exc:
                logger.error(f"Failed to process order: {exc}")
        logger.info(f"check_pending_orders: polled={len(new_orders)} processed={processed}")
        return {"status": "success", "polled": len(new_orders), "processed": processed}
    except Exception as exc:
        logger.error(f"check_pending_orders failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        if db:
            db.close()


@app.task(bind=True, max_retries=2, default_retry_delay=120)
def sync_google_sheets(self):
    """Every 6 hours - Sync product data to Google Sheets."""
    logger.info("Task: sync_google_sheets started")
    db = None
    try:
        db = _get_db()
        from database.crud import get_products
        products = get_products(db, limit=500)
        from config.settings import get_settings
        settings = get_settings()
        from integrations.google_sheets_api import GoogleSheetsAPI
        sheets_api = GoogleSheetsAPI(
            credentials_file=settings.google_application_credentials,
            spreadsheet_id=settings.google_sheets_id,
        )
        products_data = [
            {
                "id": p.id,
                "name": p.name,
                "purchase_price": p.purchase_price,
                "selling_price": p.selling_price,
                "platform": p.platform,
                "margin_percent": p.margin_percent or 0,
                "status": p.status,
                "wholesaler": p.wholesaler or "",
            }
            for p in products
        ]
        result = sheets_api.sync_products(products_data)
        logger.info(f"sync_google_sheets: synced {len(products_data)} products")
        return {"status": "success", "synced_count": len(products_data)}
    except Exception as exc:
        logger.error(f"sync_google_sheets failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        if db:
            db.close()
