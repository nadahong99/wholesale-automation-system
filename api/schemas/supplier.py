from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SupplierCreate(BaseModel):
    name: str
    url: Optional[str] = None
    contact_info: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    contact_info: Optional[str] = None


class SupplierResponse(BaseModel):
    id: int
    name: str
    url: Optional[str] = None
    contact_info: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
