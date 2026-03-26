# database/schemas.py
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel


# ─── Wholesaler ──────────────────────────────────────────────────────────────

class WholesalerBase(BaseModel):
    name: str
    base_url: Optional[str] = None
    is_active: bool = True


class WholesalerCreate(WholesalerBase):
    pass


class WholesalerRead(WholesalerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Product ─────────────────────────────────────────────────────────────────

class ProductBase(BaseModel):
    name: str
    category: Optional[str] = None
    wholesale_price: float
    suggested_selling_price: Optional[float] = None
    actual_selling_price: Optional[float] = None
    moq: int = 1
    image_url: Optional[str] = None
    gcs_image_url: Optional[str] = None
    description: Optional[str] = None
    wholesaler_id: Optional[int] = None
    external_product_id: Optional[str] = None
    is_active: bool = True
    is_listed: bool = False


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    actual_selling_price: Optional[float] = None
    is_active: Optional[bool] = None
    is_listed: Optional[bool] = None
    naver_product_id: Optional[str] = None
    coupang_product_id: Optional[str] = None
    gcs_image_url: Optional[str] = None


class ProductRead(ProductBase):
    id: int
    naver_product_id: Optional[str] = None
    coupang_product_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── DailyProduct ────────────────────────────────────────────────────────────

class DailyProductBase(BaseModel):
    date: date
    product_id: int
    search_volume: int = 0
    product_count_in_market: int = 0
    golden_keyword_score: float = 0.0
    approved_by_ceo: str = "pending"


class DailyProductCreate(DailyProductBase):
    pass


class DailyProductRead(DailyProductBase):
    id: int
    approved_at: Optional[datetime] = None
    sent_to_ceo_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Order ───────────────────────────────────────────────────────────────────

class OrderBase(BaseModel):
    product_id: int
    customer_order_id: Optional[str] = None
    quantity: int = 1
    wholesaler_id: Optional[int] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    wholesale_order_id: Optional[str] = None
    completed_at: Optional[datetime] = None


class OrderRead(OrderBase):
    id: int
    wholesale_order_id: Optional[str] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── DailyReport ─────────────────────────────────────────────────────────────

class DailyReportRead(BaseModel):
    id: int
    date: date
    total_sales: float
    total_cost: float
    total_profit: float
    margin_percent: float
    cash_available: float
    total_orders: int
    new_products_sourced: int
    products_approved: int
    warning_flags: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── PriceHistory ────────────────────────────────────────────────────────────

class PriceHistoryRead(BaseModel):
    id: int
    product_id: int
    date: datetime
    competitor_price: Optional[float] = None
    our_price: Optional[float] = None
    margin_percent: Optional[float] = None
    platform: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Budget ──────────────────────────────────────────────────────────────────

class BudgetRead(BaseModel):
    id: int
    date: date
    daily_budget: float
    spent: float
    remaining: float
    set_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
