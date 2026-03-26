# api/routes/orders.py
"""REST endpoints for order management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import get_db
from database import crud, schemas
from api.models import OrderRequest
from core.order_processor import process_customer_order
from utils.logger import get_logger

router = APIRouter(prefix="/orders", tags=["orders"])
logger = get_logger("api.orders")


@router.post("/", response_model=schemas.OrderRead)
def create_order(req: OrderRequest, db: Session = Depends(get_db)):
    """Place a customer order and trigger wholesaler fulfillment."""
    order = process_customer_order(
        db=db,
        product_id=req.product_id,
        customer_order_id=req.customer_order_id,
        quantity=req.quantity,
    )
    if not order:
        raise HTTPException(status_code=404, detail="Product not found.")
    return order


@router.get("/{order_id}", response_model=schemas.OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order
