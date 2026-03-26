import asyncio
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot for notifications and CEO approvals."""

    def __init__(self, token: str = "", chat_id: str = ""):
        self.token = token
        self.chat_id = chat_id
        self._app: Any = None
        if token:
            self._setup_app()

    def _setup_app(self) -> None:
        """Initialize python-telegram-bot Application."""
        try:
            from telegram.ext import Application, CommandHandler, CallbackQueryHandler
            self._app = Application.builder().token(self.token).build()
            self._app.add_handler(CommandHandler("start", self.handle_start))
            self._app.add_handler(CommandHandler("budget", self.handle_set_budget))
            self._app.add_handler(CommandHandler("check_budget", self.handle_check_budget))
            self._app.add_handler(CallbackQueryHandler(self.handle_callback_query))
            logger.info("TelegramBot application configured")
        except Exception as exc:
            logger.warning(f"TelegramBot setup failed (token may be invalid): {exc}")

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a text message to the configured chat."""
        if not self.token or not self.chat_id:
            logger.debug(f"[TelegramBot mock] send_message: {text[:80]}")
            return False
        try:
            from telegram import Bot
            bot = Bot(token=self.token)
            await bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode,
            )
            logger.info(f"Telegram message sent ({len(text)} chars)")
            return True
        except Exception as exc:
            logger.error(f"Failed to send Telegram message: {exc}")
            return False

    async def send_product_approval_request(self, product_data: Dict) -> bool:
        """Send product details with approve/reject inline buttons to CEO."""
        if not self.token or not self.chat_id:
            logger.debug(f"[TelegramBot mock] approval request for {product_data.get('name')}")
            return False
        try:
            from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
            bot = Bot(token=self.token)
            product_id = product_data.get("id", 0)
            text = (
                f"<b>🛒 신규 상품 승인 요청</b>\n\n"
                f"📦 상품명: {product_data.get('name', 'N/A')}\n"
                f"💰 매입가: {product_data.get('purchase_price', 0):,}원\n"
                f"💵 판매가: {product_data.get('selling_price', 0):,}원\n"
                f"📊 마진율: {product_data.get('margin_percent', 0):.1f}%\n"
                f"📦 MOQ: {product_data.get('moq', 1)}개\n"
                f"🏪 도매처: {product_data.get('wholesaler', 'N/A')}\n"
            )
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ 승인", callback_data=f"approve_{product_id}"),
                    InlineKeyboardButton("❌ 거절", callback_data=f"reject_{product_id}"),
                ]
            ])
            await bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            logger.info(f"Approval request sent for product {product_id}")
            return True
        except Exception as exc:
            logger.error(f"Failed to send approval request: {exc}")
            return False

    async def handle_start(self, update: Any, context: Any) -> None:
        """Handle /start command."""
        welcome = (
            "🤖 <b>도매 자동화 봇</b>에 오신 것을 환영합니다!\n\n"
            "📋 <b>명령어 안내:</b>\n"
            "/budget [금액] - 일일 예산 설정\n"
            "/check_budget - 현재 예산 확인\n"
        )
        await update.message.reply_html(welcome)

    async def handle_set_budget(self, update: Any, context: Any) -> None:
        """Handle /budget [amount] command."""
        try:
            args = context.args
            if not args:
                await update.message.reply_text("사용법: /budget 500000")
                return
            amount = int(args[0].replace(",", "").replace("원", ""))
            await update.message.reply_html(
                f"✅ 일일 예산이 <b>{amount:,}원</b>으로 설정되었습니다."
            )
            logger.info(f"Budget set to {amount} via Telegram")
        except (ValueError, IndexError) as exc:
            await update.message.reply_text(f"오류: {exc}\n사용법: /budget 500000")

    async def handle_check_budget(self, update: Any, context: Any) -> None:
        """Handle /check_budget command."""
        try:
            from database.session import get_session_factory
            from database.crud import get_budget_status
            from datetime import date
            factory = get_session_factory()
            db = factory()
            budget = get_budget_status(db, date.today())
            db.close()
            if budget:
                pct = (budget.spent_amount / max(budget.daily_budget, 1)) * 100
                text = (
                    f"📊 <b>오늘의 예산 현황</b>\n"
                    f"총 예산: {budget.daily_budget:,}원\n"
                    f"사용액: {budget.spent_amount:,}원 ({pct:.1f}%)\n"
                    f"잔여액: {budget.remaining:,}원"
                )
            else:
                text = "오늘의 예산 정보가 없습니다."
            await update.message.reply_html(text)
        except Exception as exc:
            await update.message.reply_text(f"오류가 발생했습니다: {exc}")

    async def handle_callback_query(self, update: Any, context: Any) -> None:
        """Handle product approve/reject callbacks."""
        query = update.callback_query
        await query.answer()
        data = query.data or ""
        if data.startswith("approve_"):
            product_id = data.split("_", 1)[1]
            await query.edit_message_text(
                f"✅ 상품 #{product_id} 승인 완료되었습니다.", parse_mode="HTML"
            )
            logger.info(f"Product {product_id} approved via Telegram")
        elif data.startswith("reject_"):
            product_id = data.split("_", 1)[1]
            await query.edit_message_text(
                f"❌ 상품 #{product_id} 거절되었습니다.", parse_mode="HTML"
            )
            logger.info(f"Product {product_id} rejected via Telegram")

    async def send_daily_report(self, report_data: Dict) -> bool:
        """Send formatted daily business report."""
        text = (
            f"📈 <b>일일 리포트 - {report_data.get('date', 'N/A')}</b>\n\n"
            f"💰 총 매출: {report_data.get('total_revenue', 0):,}원\n"
            f"📦 주문 수: {report_data.get('order_count', 0)}건\n"
            f"💵 순이익: {report_data.get('net_profit', 0):,}원\n"
            f"📊 마진율: {report_data.get('margin_percent', 0):.1f}%\n"
            f"🏪 소싱 상품: {report_data.get('sourced_products', 0)}개\n"
        )
        return await self.send_message(text)

    async def send_cash_warning(self, current_cash: int) -> bool:
        """Send a cash balance warning when balance is critically low."""
        text = (
            f"⚠️ <b>현금 잔고 경고</b>\n\n"
            f"현재 잔고: <b>{current_cash:,}원</b>\n"
            f"기준 금액: 100,000원 이하\n\n"
            f"즉시 자금 보충이 필요합니다!"
        )
        return await self.send_message(text)

    def run_bot(self) -> None:
        """Start the bot polling loop (blocking)."""
        if self._app is None:
            logger.error("TelegramBot not configured - missing token")
            return
        logger.info("Starting Telegram bot polling...")
        self._app.run_polling(allowed_updates=["message", "callback_query"])
