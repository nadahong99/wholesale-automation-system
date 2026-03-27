from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class OrderCreate(BaseModel):
    order_number: str
    product_id: int
    quantity: int
    unit_price: float
    total_price: float
    status: str = "pending"
    order_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None


class OrderUpdate(BaseModel):
    quantity: Optional[int] = None
    status: Optional[str] = None
    delivery_date: Optional[datetime] = None


class OrderResponse(BaseModel):
    id: int
    order_number: str
    product_id: int
    quantity: int
    unit_price: float
    total_price: float
    status: str
    order_date: datetime
    delivery_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
