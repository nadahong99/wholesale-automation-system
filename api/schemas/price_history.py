from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PriceHistoryCreate(BaseModel):
    product_id: int
    old_price: float
    new_price: float
    change_percentage: Optional[float] = None
    recorded_at: Optional[datetime] = None


class PriceHistoryResponse(BaseModel):
    id: int
    product_id: int
    old_price: float
    new_price: float
    change_percentage: Optional[float] = None
    recorded_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
