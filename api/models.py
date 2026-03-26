# api/models.py
"""Pydantic request/response models for the API layer."""
from typing import Optional, List
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"


class SourcingTriggerRequest(BaseModel):
    target_per_wholesaler: Optional[int] = None


class SourcingTriggerResponse(BaseModel):
    total_products: int
    message: str


class PriceMonitorResponse(BaseModel):
    adjusted: int
    message: str


class OrderRequest(BaseModel):
    product_id: int
    customer_order_id: str
    quantity: int = 1


class BudgetSetRequest(BaseModel):
    amount: float
    set_by: str = "CEO"


class GoldenKeywordFilterResponse(BaseModel):
    sent_to_ceo: int
    message: str
