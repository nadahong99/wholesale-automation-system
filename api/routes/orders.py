import logging
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.session import get_db
from database.crud import (
    create_order, get_order, get_orders, update_order_status,
    get_todays_orders, calculate_daily_profit,
)
from database.schemas import OrderCreate, OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[OrderResponse])
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List orders with optional filters."""
    return get_orders(db, skip=skip, limit=limit, status=status, platform=platform)


@router.get("/summary")
def orders_summary(db: Session = Depends(get_db)):
    """Get today's order summary statistics."""
    todays_orders = get_todays_orders(db)
    total_revenue = sum(o.total_amount for o in todays_orders)
    daily_profit = calculate_daily_profit(db)
    platform_breakdown: dict = {}
    for order in todays_orders:
        platform_breakdown[order.platform] = platform_breakdown.get(order.platform, 0) + order.total_amount
    return {
        "date": date.today().isoformat(),
        "total_orders": len(todays_orders),
        "total_revenue": total_revenue,
        "daily_profit": daily_profit,
        "platform_breakdown": platform_breakdown,
        "status_breakdown": {
            s: sum(1 for o in todays_orders if o.status == s)
            for s in set(o.status for o in todays_orders)
        },
    }


@router.get("/{order_id}", response_model=OrderResponse)
def get_single_order(order_id: int, db: Session = Depends(get_db)):
    """Get details for a specific order."""
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/process")
def process_orders(db: Session = Depends(get_db)):
    """Trigger order polling and processing from all platforms."""
    try:
        from core.order_processor import OrderProcessor
        processor = OrderProcessor(db_session=db)
        new_orders = processor.poll_new_orders()
        processed = []
        for order_data in new_orders:
            try:
                result = processor.process_order(order_data)
                processed.append(result)
            except Exception as exc:
                logger.error(f"Failed to process order {order_data.get('order_number')}: {exc}")
        return {
            "polled": len(new_orders),
            "processed": len(processed),
            "orders": processed,
        }
    except Exception as exc:
        logger.error(f"Order processing failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/{order_id}/status")
def update_status(order_id: int, status: str, db: Session = Depends(get_db)):
    """Update the status of an order."""
    from config.constants import ORDER_STATUS
    if status not in ORDER_STATUS:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {ORDER_STATUS}")
    order = update_order_status(db, order_id, status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    logger.info(f"Order {order_id} status -> {status}")
    return {"id": order_id, "status": status}


@router.post("/reconcile")
def reconcile(db: Session = Depends(get_db)):
    """Trigger settlement reconciliation for delivered orders."""
    from core.order_processor import OrderProcessor
    processor = OrderProcessor(db_session=db)
    result = processor.reconcile_settlements()
    return result
