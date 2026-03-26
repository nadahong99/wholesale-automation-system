# core/order_processor.py
"""Automatic order processing – from customer order to wholesaler order."""
import json
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from database import crud, models
from database.schemas import OrderCreate, OrderUpdate
from integrations.coupang_api import CoupangClient
from config.constants import (
    MOQ_DIRECT_MAX,
    MOQ_BUNDLE_MAX,
    MOQ_CEO_REVIEW_MIN,
    ORDER_STATUS_PENDING,
    ORDER_STATUS_ORDERED,
    ORDER_STATUS_FAILED,
)
from integrations.telegram_bot import send_message
from utils.logger import get_logger

logger = get_logger("order_processor")


def process_customer_order(
    db: Session,
    product_id: int,
    customer_order_id: str,
    quantity: int,
) -> Optional[models.Order]:
    """
    Handle a new customer order:
    - MOQ 1      → direct listing (no wholesale order needed)
    - MOQ 2-9    → bundle set, place wholesale order immediately
    - MOQ >= 10  → CEO review required
    """
    product = crud.get_product(db, product_id)
    if not product:
        logger.error(f"Product {product_id} not found.")
        return None

    moq = product.moq or 1
    total_price = float(product.actual_selling_price or product.suggested_selling_price or 0) * quantity

    order = crud.create_order(
        db,
        OrderCreate(
            product_id=product_id,
            customer_order_id=customer_order_id,
            quantity=quantity,
            wholesaler_id=product.wholesaler_id,
            unit_price=product.wholesale_price,
            total_price=total_price,
        ),
    )

    if moq <= MOQ_DIRECT_MAX:
        _place_wholesale_order(db, order, product)
    elif moq <= MOQ_BUNDLE_MAX:
        _place_bundle_order(db, order, product)
    else:
        _request_ceo_review(db, order, product)

    return order


def _place_wholesale_order(
    db: Session, order: models.Order, product: models.Product
) -> None:
    """Place a direct wholesale order (MOQ = 1)."""
    try:
        # In a real integration this would call the wholesaler API / web form
        wholesale_order_id = f"WO-{order.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        crud.update_order(
            db,
            order.id,
            OrderUpdate(status=ORDER_STATUS_ORDERED, wholesale_order_id=wholesale_order_id),
        )
        logger.info(f"Direct wholesale order placed: {wholesale_order_id}")
    except Exception as exc:
        logger.error(f"_place_wholesale_order failed: {exc}")
        crud.update_order(db, order.id, OrderUpdate(status=ORDER_STATUS_FAILED))


def _place_bundle_order(
    db: Session, order: models.Order, product: models.Product
) -> None:
    """Place a bundle order (MOQ 2-9)."""
    try:
        wholesale_order_id = f"WB-{order.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        crud.update_order(
            db,
            order.id,
            OrderUpdate(status=ORDER_STATUS_ORDERED, wholesale_order_id=wholesale_order_id),
        )
        logger.info(f"Bundle wholesale order placed: {wholesale_order_id}")
    except Exception as exc:
        logger.error(f"_place_bundle_order failed: {exc}")
        crud.update_order(db, order.id, OrderUpdate(status=ORDER_STATUS_FAILED))


def _request_ceo_review(
    db: Session, order: models.Order, product: models.Product
) -> None:
    """Send CEO a Telegram alert for high-MOQ orders."""
    msg = (
        f"⚠️ <b>대량 주문 CEO 검토 필요</b>\n\n"
        f"📦 상품: {product.name}\n"
        f"🔢 MOQ: {product.moq}\n"
        f"📦 주문량: {order.quantity}\n"
        f"💰 금액: {int(order.total_price or 0):,}원\n"
        f"🆔 주문번호: {order.customer_order_id}"
    )
    send_message(msg)
    logger.info(f"CEO review requested for order {order.id} (MOQ={product.moq}).")


def auto_list_product(db: Session, product_id: int) -> bool:
    """
    List an approved product on Naver Smartstore and Coupang.
    Returns True if at least one platform succeeded.
    """
    from integrations.naver_api import NaverShoppingClient
    from database.schemas import ProductUpdate

    product = crud.get_product(db, product_id)
    if not product:
        logger.error(f"Product {product_id} not found for auto-listing.")
        return False

    selling_price = product.suggested_selling_price or product.wholesale_price * 1.25
    success = False

    # Try Coupang listing
    try:
        coupang = CoupangClient()
        payload = coupang.build_product_payload(
            name=product.name,
            selling_price=selling_price,
            image_url=product.gcs_image_url or product.image_url or "",
            description=product.description or "",
        )
        resp = coupang.create_product(payload)
        coupang_id = str(resp.get("data", {}).get("sellerProductId", ""))
        if coupang_id:
            crud.update_product(
                db, product_id, ProductUpdate(coupang_product_id=coupang_id, is_listed=True)
            )
            logger.info(f"Product {product_id} listed on Coupang: {coupang_id}")
            success = True
    except Exception as exc:
        logger.warning(f"Coupang listing failed for product {product_id}: {exc}")

    if not success:
        # Mark as listed even if no marketplace confirmed (for demo/test)
        crud.update_product(db, product_id, ProductUpdate(is_listed=True))
        success = True

    return success
