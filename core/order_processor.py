import logging
import random
import string
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def _random_order_number(prefix: str = "ORD") -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"{prefix}-{suffix}"


class OrderProcessor:
    """Handles order polling, processing, and wholesaler coordination."""

    def __init__(self, db_session=None):
        self.db = db_session
        self._pending_orders: List[Dict] = []

    def poll_new_orders(self) -> List[Dict]:
        """Poll Naver and Coupang for new orders (mock implementation)."""
        new_orders = []
        for platform in ["naver", "coupang"]:
            count = random.randint(0, 3)
            for _ in range(count):
                order = {
                    "order_number": _random_order_number(platform[:3].upper()),
                    "platform": platform,
                    "quantity": random.randint(1, 5),
                    "unit_price": random.randint(15000, 80000),
                    "status": "PENDING",
                    "customer_name": "홍길동",
                    "shipping_address": "서울시 강남구 테헤란로 123",
                    "created_at": datetime.utcnow().isoformat(),
                }
                order["total_amount"] = order["unit_price"] * order["quantity"]
                new_orders.append(order)

        self._pending_orders.extend(new_orders)
        logger.info(f"Polled {len(new_orders)} new orders from platforms")
        return new_orders

    def process_order(self, order_data: Dict) -> Dict:
        """Validate, enrich, and persist an order."""
        required = ["order_number", "platform", "unit_price", "quantity"]
        for field in required:
            if field not in order_data:
                raise ValueError(f"Missing required field: {field}")

        order_data.setdefault("total_amount", order_data["unit_price"] * order_data["quantity"])
        order_data["status"] = "CONFIRMED"
        order_data["processed_at"] = datetime.utcnow().isoformat()

        if self.db:
            try:
                from database.crud import create_order
                from database.schemas import OrderCreate
                schema = OrderCreate(
                    platform=order_data["platform"],
                    order_number=order_data["order_number"],
                    quantity=order_data["quantity"],
                    unit_price=order_data["unit_price"],
                    total_amount=order_data["total_amount"],
                    status=order_data["status"],
                )
                create_order(self.db, schema)
            except Exception as exc:
                logger.error(f"Failed to persist order: {exc}")

        logger.info(
            f"Processed order {order_data['order_number']} "
            f"platform={order_data['platform']} amount={order_data['total_amount']}"
        )
        return order_data

    def auto_order_from_wholesaler(self, product: Dict, quantity: int) -> Dict:
        """Simulate placing a purchase order with the wholesaler."""
        wholesaler = product.get("wholesaler", "unknown")
        po_number = _random_order_number("PO")
        total_cost = product["purchase_price"] * quantity
        result = {
            "po_number": po_number,
            "wholesaler": wholesaler,
            "product_name": product.get("name", ""),
            "quantity": quantity,
            "unit_cost": product["purchase_price"],
            "total_cost": total_cost,
            "status": "SUBMITTED",
            "submitted_at": datetime.utcnow().isoformat(),
        }
        logger.info(
            f"Auto-order submitted: PO={po_number} wholesaler={wholesaler} "
            f"qty={quantity} total={total_cost}"
        )
        return result

    def update_order_status(self, order_id: int, status: str) -> Dict:
        """Update order status in the database."""
        if self.db:
            from database.crud import update_order_status as db_update
            order = db_update(self.db, order_id, status)
            if order:
                logger.info(f"Order {order_id} status updated to {status}")
                return {"id": order_id, "status": status, "updated": True}
        return {"id": order_id, "status": status, "updated": False}

    def get_pending_orders(self) -> List[Dict]:
        """Return orders with PENDING status."""
        if self.db:
            from database.crud import get_orders
            orders = get_orders(self.db, status="PENDING")
            return [
                {
                    "id": o.id,
                    "order_number": o.order_number,
                    "platform": o.platform,
                    "total_amount": o.total_amount,
                    "status": o.status,
                }
                for o in orders
            ]
        return [o for o in self._pending_orders if o.get("status") == "PENDING"]

    def reconcile_settlements(self) -> Dict:
        """Reconcile delivered orders to confirm settlements."""
        if self.db:
            from database.crud import get_orders, update_order_status as db_update
            delivered = get_orders(self.db, status="DELIVERED")
            reconciled = 0
            total_amount = 0
            for order in delivered:
                db_update(self.db, order.id, "CONFIRMED")
                reconciled += 1
                total_amount += order.total_amount
            logger.info(f"Reconciled {reconciled} orders totaling {total_amount} KRW")
            return {"reconciled_count": reconciled, "total_amount": total_amount}
        return {"reconciled_count": 0, "total_amount": 0}

    def handle_failed_order(self, order_id: int, reason: str) -> Dict:
        """Mark an order as failed and log the reason."""
        logger.error(f"Order {order_id} failed: {reason}")
        if self.db:
            self.update_order_status(order_id, "CANCELLED")
        return {
            "order_id": order_id,
            "status": "CANCELLED",
            "reason": reason,
            "handled_at": datetime.utcnow().isoformat(),
        }
