# integrations/telegram_bot.py
"""Telegram Bot for CEO product approval and reporting."""
import asyncio
import json
from datetime import datetime, date
from typing import Optional, List
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from config.settings import settings
from utils.logger import get_logger

logger = get_logger("telegram_bot")


# ─── Simple one-shot message sender ──────────────────────────────────────────

async def send_message_async(text: str, chat_id: Optional[str] = None, parse_mode: str = "HTML") -> bool:
    """Send a plain text message to the CEO chat."""
    chat_id = chat_id or settings.TELEGRAM_CEO_CHAT_ID
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        logger.warning("Telegram credentials not set.")
        return False
    try:
        bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
        return True
    except Exception as exc:
        logger.error(f"Telegram send failed: {exc}")
        return False


def send_message(text: str, chat_id: Optional[str] = None) -> bool:
    """Synchronous wrapper around *send_message_async*."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(send_message_async(text, chat_id))
            return True
        return loop.run_until_complete(send_message_async(text, chat_id))
    except Exception as exc:
        logger.error(f"send_message error: {exc}")
        return False


async def send_product_for_approval_async(
    daily_product_id: int,
    product_name: str,
    wholesale_price: float,
    selling_price: float,
    margin_percent: float,
    search_volume: int,
    golden_score: float,
    image_url: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> bool:
    """Send a product to CEO with Approve/Reject inline keyboard."""
    chat_id = chat_id or settings.TELEGRAM_CEO_CHAT_ID
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        logger.warning("Telegram credentials not set.")
        return False

    text = (
        f"🛍️ <b>신규 상품 승인 요청</b>\n\n"
        f"📦 <b>상품명:</b> {product_name}\n"
        f"💰 <b>도매가:</b> {int(wholesale_price):,}원\n"
        f"🏷️ <b>판매가:</b> {int(selling_price):,}원\n"
        f"📈 <b>마진율:</b> {margin_percent:.1f}%\n"
        f"🔍 <b>검색량:</b> {search_volume:,}\n"
        f"⭐ <b>황금키워드 점수:</b> {golden_score:.1f}\n"
        f"\n<i>승인하시면 Naver/Coupang에 자동 등록됩니다.</i>"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ 승인", callback_data=f"approve:{daily_product_id}"
                ),
                InlineKeyboardButton(
                    "❌ 거절", callback_data=f"reject:{daily_product_id}"
                ),
            ]
        ]
    )

    try:
        bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
        if image_url:
            try:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=image_url,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
                return True
            except Exception:
                pass
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return True
    except Exception as exc:
        logger.error(f"send_product_for_approval failed: {exc}")
        return False


def send_product_for_approval(
    daily_product_id: int,
    product_name: str,
    wholesale_price: float,
    selling_price: float,
    margin_percent: float,
    search_volume: int,
    golden_score: float,
    image_url: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> bool:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(
                send_product_for_approval_async(
                    daily_product_id, product_name, wholesale_price,
                    selling_price, margin_percent, search_volume, golden_score,
                    image_url, chat_id,
                )
            )
            return True
        return loop.run_until_complete(
            send_product_for_approval_async(
                daily_product_id, product_name, wholesale_price,
                selling_price, margin_percent, search_volume, golden_score,
                image_url, chat_id,
            )
        )
    except Exception as exc:
        logger.error(f"send_product_for_approval error: {exc}")
        return False


# ─── Bot application ──────────────────────────────────────────────────────────

async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 안녕하세요! 도매 자동화 시스템입니다.\n\n"
        "/set_budget [금액] - 일일 예산 설정\n"
        "/check_budget - 예산 확인\n"
        "/sales_report - 오늘 판매 리포트\n"
        "/top_products - 상위 판매 상품"
    )


async def _set_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from database.session import SessionLocal
    from database.crud import set_daily_budget

    chat_id = str(update.effective_chat.id)
    if chat_id != settings.TELEGRAM_CEO_CHAT_ID:
        await update.message.reply_text("⛔ 권한 없음")
        return

    try:
        amount = float(context.args[0].replace(",", ""))
        db = SessionLocal()
        try:
            budget = set_daily_budget(db, amount, set_by="CEO")
            await update.message.reply_text(
                f"✅ 일일 예산이 {int(budget.daily_budget):,}원으로 설정되었습니다."
            )
        finally:
            db.close()
    except (IndexError, ValueError):
        await update.message.reply_text("사용법: /set_budget 1000000")


async def _check_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from database.session import SessionLocal
    from database.crud import get_or_create_budget

    db = SessionLocal()
    try:
        budget = get_or_create_budget(db)
        await update.message.reply_text(
            f"💰 <b>예산 현황</b>\n\n"
            f"일일 예산: {int(budget.daily_budget):,}원\n"
            f"사용 금액: {int(budget.spent):,}원\n"
            f"남은 금액: {int(budget.remaining):,}원",
            parse_mode="HTML",
        )
    finally:
        db.close()


async def _sales_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from database.session import SessionLocal
    from database.crud import get_or_create_daily_report

    db = SessionLocal()
    try:
        report = get_or_create_daily_report(db, datetime.utcnow().date())
        await update.message.reply_text(
            f"📊 <b>오늘 판매 리포트 ({report.date})</b>\n\n"
            f"총 매출: {int(report.total_sales):,}원\n"
            f"총 원가: {int(report.total_cost):,}원\n"
            f"총 이익: {int(report.total_profit):,}원\n"
            f"마진율: {report.margin_percent:.1f}%\n"
            f"주문 수: {report.total_orders}건\n"
            f"신규 소싱: {report.new_products_sourced}개\n"
            f"CEO 승인: {report.products_approved}개",
            parse_mode="HTML",
        )
    finally:
        db.close()


async def _top_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from database.session import SessionLocal
    from database import models
    from sqlalchemy import func, desc

    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        results = (
            db.query(
                models.Product.name,
                func.count(models.Order.id).label("order_count"),
                func.sum(models.Order.total_price).label("revenue"),
            )
            .join(models.Order, models.Order.product_id == models.Product.id)
            .filter(func.date(models.Order.created_at) == today)
            .group_by(models.Product.id)
            .order_by(desc("revenue"))
            .limit(5)
            .all()
        )

        if not results:
            await update.message.reply_text("오늘 판매된 상품이 없습니다.")
            return

        lines = ["🏆 <b>오늘 상위 판매 상품 TOP 5</b>\n"]
        for i, (name, count, revenue) in enumerate(results, 1):
            lines.append(f"{i}. {name}\n   주문: {count}건 | 매출: {int(revenue or 0):,}원")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    finally:
        db.close()


async def _callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Approve / Reject inline button presses."""
    query = update.callback_query
    await query.answer()

    data = query.data  # e.g. "approve:42" or "reject:42"
    action, dp_id_str = data.split(":", 1)
    daily_product_id = int(dp_id_str)

    from database.session import SessionLocal
    from database.crud import approve_daily_product, reject_daily_product
    from core.order_processor import auto_list_product

    db = SessionLocal()
    try:
        if action == "approve":
            dp = approve_daily_product(db, daily_product_id)
            if dp:
                # Trigger auto-listing
                try:
                    auto_list_product(db, dp.product_id)
                except Exception as exc:
                    logger.error(f"auto_list_product failed: {exc}")
                await query.edit_message_text(
                    f"✅ 승인 완료! 상품이 Naver/Coupang에 등록됩니다.\n(ID: {daily_product_id})"
                )
        elif action == "reject":
            reject_daily_product(db, daily_product_id)
            await query.edit_message_text(f"❌ 거절 처리되었습니다. (ID: {daily_product_id})")
    finally:
        db.close()


def build_application() -> Application:
    """Build and return the Telegram Application."""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set.")

    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", _start))
    app.add_handler(CommandHandler("set_budget", _set_budget))
    app.add_handler(CommandHandler("check_budget", _check_budget))
    app.add_handler(CommandHandler("sales_report", _sales_report))
    app.add_handler(CommandHandler("top_products", _top_products))
    app.add_handler(CallbackQueryHandler(_callback_handler))
    return app


def run_bot():
    """Start the Telegram bot (blocking)."""
    app = build_application()
    logger.info("Starting Telegram bot...")
    app.run_polling()
