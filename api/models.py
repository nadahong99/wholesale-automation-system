from datetime import datetime, date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourcingRequest(BaseModel):
    run_golden_filter: bool = True
    min_margin_percent: float = 20.0
    platforms: List[str] = ["naver", "coupang"]


class SourcingResponse(BaseModel):
    total_scraped: int
    golden_keyword_matches: int
    auto_list_count: int
    bundle_count: int
    ceo_review_count: int
    below_margin_count: int
    total_actionable: int
    errors: List[str] = []
    triggered_at: datetime = Field(default_factory=datetime.utcnow)


class OrderCreateRequest(BaseModel):
    product_id: Optional[int] = None
    platform: str
    order_number: str
    quantity: int = Field(ge=1)
    unit_price: int = Field(ge=0)
    total_amount: Optional[int] = None

    def model_post_init(self, __context) -> None:
        if self.total_amount is None:
            self.total_amount = self.unit_price * self.quantity


class OrderResponse(BaseModel):
    id: int
    platform: str
    order_number: str
    quantity: int
    unit_price: int
    total_amount: int
    status: str
    created_at: datetime


class BudgetSetRequest(BaseModel):
    daily_budget: int = Field(ge=1000, description="Daily budget in KRW")
    date: Optional[date] = None


class BudgetResponse(BaseModel):
    date: date
    daily_budget: int
    spent_amount: int
    remaining: int
    utilization_percent: float


class ProductApprovalRequest(BaseModel):
    product_id: int
    approved: bool
    reason: Optional[str] = None


class DashboardData(BaseModel):
    date: date
    total_revenue: int
    total_expense: int
    net_profit: int
    order_count: int
    margin_percent: float
    cash_balance: int
    sourced_today: int
    top_products: List[Dict[str, Any]] = []
    alerts: List[str] = []


class PriceMonitorRequest(BaseModel):
    product_ids: Optional[List[int]] = None
    platforms: List[str] = ["naver", "coupang"]


class ReportRequest(BaseModel):
    start_date: date
    end_date: date
    include_products: bool = True
    include_orders: bool = True
    include_cash_flow: bool = True


class ReportResponse(BaseModel):
    period_start: date
    period_end: date
    total_revenue: int
    total_expense: int
    net_profit: int
    total_orders: int
    average_margin: float
    top_platforms: Dict[str, int] = {}
    generated_at: datetime = Field(default_factory=datetime.utcnow)
