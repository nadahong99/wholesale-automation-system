from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, field_validator, ConfigDict


class ProductCreate(BaseModel):
    name: str
    purchase_price: int
    selling_price: int
    platform: str = "naver"
    url: Optional[str] = None
    image_url: Optional[str] = None
    moq: int = 1
    status: str = "SOURCED"
    keyword: Optional[str] = None
    wholesaler: Optional[str] = None
    category: Optional[str] = None
    margin_percent: Optional[float] = None

    @field_validator("purchase_price", "selling_price")
    @classmethod
    def price_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Price must be non-negative")
        return v

    @field_validator("moq")
    @classmethod
    def moq_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("MOQ must be at least 1")
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    selling_price: Optional[int] = None
    status: Optional[str] = None
    margin_percent: Optional[float] = None
    image_url: Optional[str] = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    purchase_price: int
    selling_price: int
    platform: str
    url: Optional[str]
    image_url: Optional[str]
    moq: int
    status: str
    keyword: Optional[str]
    wholesaler: Optional[str]
    category: Optional[str]
    margin_percent: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]


class OrderCreate(BaseModel):
    product_id: Optional[int] = None
    platform: str
    order_number: str
    quantity: int = 1
    unit_price: int
    total_amount: int
    status: str = "PENDING"


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: Optional[int]
    platform: str
    order_number: str
    quantity: int
    unit_price: int
    total_amount: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]


class TransactionCreate(BaseModel):
    order_id: Optional[int] = None
    type: str
    amount: int
    description: Optional[str] = None
    category: Optional[str] = None

    @field_validator("type")
    @classmethod
    def type_must_be_valid(cls, v: str) -> str:
        if v not in ("income", "expense"):
            raise ValueError("type must be 'income' or 'expense'")
        return v


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: Optional[int]
    type: str
    amount: int
    description: Optional[str]
    category: Optional[str]
    created_at: datetime


class BudgetCreate(BaseModel):
    date: date
    daily_budget: int = 500000
    spent_amount: int = 0
    remaining: Optional[int] = None

    def model_post_init(self, __context) -> None:
        if self.remaining is None:
            self.remaining = self.daily_budget - self.spent_amount


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    daily_budget: int
    spent_amount: int
    remaining: int
    created_at: datetime


class CashFlowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    opening_balance: int
    closing_balance: int
    total_income: int
    total_expense: int
    net_flow: int
    created_at: datetime


class KeywordStatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword: str
    search_volume: int
    product_count: int
    ratio: float
    is_golden: bool
    checked_at: datetime
