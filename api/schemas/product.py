from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProductCreate(BaseModel):
    supplier_id: int
    product_code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[float] = None
    unit: Optional[str] = None
    stock: int = 0
    sku: Optional[str] = None
    sourcing_link: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[float] = None
    unit: Optional[str] = None
    stock: Optional[int] = None
    sku: Optional[str] = None
    sourcing_link: Optional[str] = None


class ProductResponse(BaseModel):
    id: int
    supplier_id: int
    product_code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[float] = None
    unit: Optional[str] = None
    stock: int
    sku: Optional[str] = None
    sourcing_link: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
