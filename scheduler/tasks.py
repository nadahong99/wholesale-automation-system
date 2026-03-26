# scheduler/tasks.py
"""Celery tasks for the daily wholesale automation workflow."""
import json
from datetime import datetime
from celery import shared_task
from scheduler.celery_app import celery_app
from utils.logger import get_logger
from integrations.telegram_bot import send_message

logger = get_logger("tasks")


# ─── 06:00 / 14:00 – Auto Sourcing ───────────────────────────────────────────

@celery_app.task(name="scheduler.tasks.auto_sourcing", bind=True, max_retries=3)
def auto_sourcing(self):
    """Scrape all 6 wholesalers and persist new products."""
    logger.info("Task started: auto_sourcing")
    try:
        from core.sourcing_engine import run_sourcing
        total = run_sourcing()
        msg = f"✅ 자동 소싱 완료: {total}개 신규 상품 수집 ({datetime.now().strftime('%H:%M')})"
        send_message(msg)
        logger.info(msg)
        return {"status": "ok", "total": total}
    except Exception as exc:
        logger.error(f"auto_sourcing failed: {exc}")
        send_message(f"❌ 자동 소싱 실패: {exc}")
        raise self.retry(exc=exc, countdown=300)


# ─── 09:00 – Golden Keyword Filter ───────────────────────────────────────────

@celery_app.task(name="scheduler.tasks.golden_keyword_filter", bind=True, max_retries=2)
def golden_keyword_filter(self):
    """
    Fetch search volumes for today's sourced products, apply golden-keyword
    filter, and send top candidates to CEO via Telegram.
    """
    logger.info("Task started: golden_keyword_filter")
    try:
        from datetime import date
        from database.session import SessionLocal
        from database import crud, models
        from database.schemas import DailyProductCreate
        from core.margin_calculator import GoldenKeywordFilter
        from integrations.naver_api import NaverDatalabClient, NaverShoppingClient
        from integrations.telegram_bot import send_product_for_approval

        db = SessionLocal()
        datalab = NaverDatalabClient()
        shopping = NaverShoppingClient()
        gk_filter = GoldenKeywordFilter()

        today = date.today()

        try:
            # Get products sourced today (not yet processed for golden keyword)
            products = (
                db.query(models.Product)
                .filter(
                    models.Product.is_active == True,
                    models.Product.created_at >= datetime.combine(today, datetime.min.time()),
                )
                .limit(500)
                .all()
            )

            candidates = []
            for p in products:
                sv = datalab.get_search_volume(p.name)
                pc = shopping.get_product_count(p.name)
                candidates.append(
                    {
                        "product_id": p.id,
                        "name": p.name,
                        "wholesale_price": p.wholesale_price,
                        "suggested_selling_price": p.suggested_selling_price,
                        "image_url": p.gcs_image_url or p.image_url,
                        "search_volume": sv,
                        "product_count_in_market": pc,
                    }
                )

            golden = gk_filter.filter_products(candidates, min_results=0, max_results=100)

            sent = 0
            for item in golden:
                dp = crud.create_daily_product(
                    db,
                    DailyProductCreate(
                        date=today,
                        product_id=item["product_id"],
                        search_volume=item["search_volume"],
                        product_count_in_market=item["product_count_in_market"],
                        golden_keyword_score=item["golden_keyword_score"],
                    ),
                )
                # Mark as sent
                dp.sent_to_ceo_at = datetime.utcnow()
                db.commit()

                from utils.helpers import calculate_margin
                margin = calculate_margin(
                    item["wholesale_price"],
                    item.get("suggested_selling_price") or item["wholesale_price"] * 1.25,
                )
                send_product_for_approval(
                    daily_product_id=dp.id,
                    product_name=item["name"],
                    wholesale_price=item["wholesale_price"],
                    selling_price=item.get("suggested_selling_price") or item["wholesale_price"] * 1.25,
                    margin_percent=margin,
                    search_volume=item["search_volume"],
                    golden_score=item["golden_keyword_score"],
                    image_url=item.get("image_url"),
                )
                sent += 1

            logger.info(f"golden_keyword_filter: {sent} products sent to CEO.")
            return {"status": "ok", "sent": sent}
        finally:
            db.close()
    except Exception as exc:
        logger.error(f"golden_keyword_filter failed: {exc}")
        send_message(f"❌ 황금 키워드 필터 실패: {exc}")
        raise self.retry(exc=exc, countdown=300)


# ─── 16:00 / Hourly – Price Monitoring ───────────────────────────────────────

@celery_app.task(name="scheduler.tasks.price_monitoring", bind=True, max_retries=2)
def price_monitoring(self):
    """Run competitor price checks and auto-adjust prices."""
    logger.info("Task started: price_monitoring")
    try:
        from monitoring.price_monitor import run_price_monitoring
        adjusted = run_price_monitoring()
        logger.info(f"price_monitoring: {adjusted} products adjusted.")
        return {"status": "ok", "adjusted": adjusted}
    except Exception as exc:
        logger.error(f"price_monitoring failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


# ─── 20:00 – Daily Report ─────────────────────────────────────────────────────

@celery_app.task(name="scheduler.tasks.daily_report", bind=True, max_retries=2)
def daily_report(self):
    """Compile and send daily report via Telegram + Google Sheets."""
    logger.info("Task started: daily_report")
    try:
        from datetime import date
        from database.session import SessionLocal
        from database import crud
        from monitoring.performance_tracker import compute_daily_metrics, get_top_products
        from monitoring.cash_flow_monitor import get_cash_flow_summary, check_and_alert
        from integrations.google_sheets_api import GoogleSheetsClient

        db = SessionLocal()
        try:
            today = date.today()
            metrics = compute_daily_metrics(db, today)
            cash = get_cash_flow_summary(db)
            top5 = get_top_products(db, limit=5, for_date=today)

            # Update daily report record
            report = crud.get_or_create_daily_report(db, today)
            report.total_sales = metrics["total_revenue"]
            report.total_cost = metrics["total_cost"]
            report.total_profit = metrics["total_profit"]
            report.margin_percent = metrics["margin_percent"]
            report.cash_available = cash["cash_available"]
            report.total_orders = metrics["total_orders"]

            warnings = []
            if cash["cash_available"] < 100_000:
                warnings.append("현금 잔액 10만원 미만!")
            if metrics["margin_percent"] < 15:
                warnings.append("평균 마진율 15% 미만!")
            report.warning_flags = json.dumps(warnings, ensure_ascii=False)
            db.commit()

            # Build Telegram message
            top_lines = "\n".join(
                f"  {i+1}. {p['product_name']} – ₩{int(p['revenue']):,}"
                for i, p in enumerate(top5)
            ) or "  (없음)"

            warn_text = "\n".join(f"  ⚠️ {w}" for w in warnings) if warnings else "  없음"

            msg = (
                f"📊 <b>일일 리포트 ({today})</b>\n\n"
                f"💰 총 매출: ₩{int(metrics['total_revenue']):,}\n"
                f"📉 총 원가: ₩{int(metrics['total_cost']):,}\n"
                f"💚 총 이익: ₩{int(metrics['total_profit']):,}\n"
                f"📈 마진율: {metrics['margin_percent']:.1f}%\n"
                f"📦 주문 수: {metrics['total_orders']}건\n"
                f"🏦 남은 예산: ₩{int(cash['cash_available']):,}\n\n"
                f"🏆 상위 5개 상품:\n{top_lines}\n\n"
                f"🚨 경고:\n{warn_text}"
            )
            send_message(msg)

            # Google Sheets update
            try:
                sheets = GoogleSheetsClient()
                sheets.update_daily_summary(
                    today,
                    metrics["total_revenue"],
                    metrics["total_cost"],
                    metrics["total_profit"],
                    metrics["margin_percent"],
                    metrics["total_orders"],
                )
            except Exception as exc:
                logger.warning(f"Google Sheets update failed: {exc}")

            check_and_alert(db)
            logger.info("daily_report task complete.")
            return {"status": "ok"}
        finally:
            db.close()
    except Exception as exc:
        logger.error(f"daily_report failed: {exc}")
        send_message(f"❌ 일일 리포트 생성 실패: {exc}")
        raise self.retry(exc=exc, countdown=60)
