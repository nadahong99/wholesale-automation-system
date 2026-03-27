from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class InventoryCreate(BaseModel):
    product_id: int
    warehouse_location: str
    quantity: int = 0


class InventoryUpdate(BaseModel):
    quantity: Optional[int] = None
    warehouse_location: Optional[str] = None
    last_checked: Optional[datetime] = None


class InventoryResponse(BaseModel):
    id: int
    product_id: int
    warehouse_location: str
    quantity: int
    last_checked: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
