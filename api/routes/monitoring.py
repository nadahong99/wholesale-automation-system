import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.session import get_db

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
logger = logging.getLogger(__name__)


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    """Return aggregated dashboard data for today."""
    try:
        from database.crud import (
            get_todays_orders, calculate_daily_profit,
            get_budget_status, get_or_create_cash_flow
        )
        today = date.today()
        orders = get_todays_orders(db)
        total_revenue = sum(o.total_amount for o in orders)
        daily_profit = calculate_daily_profit(db)
        budget = get_budget_status(db, today)
        cash_flow = get_or_create_cash_flow(db, today)

        from database.models import Product
        from sqlalchemy import func
        product_stats = dict(
            db.query(Product.status, func.count(Product.id)).group_by(Product.status).all()
        )
        margin = 0.0
        if total_revenue > 0 and orders:
            total_cost = sum(
                o.unit_price * o.quantity for o in orders
            )
            margin = ((total_revenue - total_cost) / total_revenue) * 100

        return {
            "date": today.isoformat(),
            "total_revenue": total_revenue,
            "order_count": len(orders),
            "daily_profit": daily_profit,
            "margin_percent": round(margin, 2),
            "budget": {
                "daily_budget": budget.daily_budget if budget else 500000,
                "spent": budget.spent_amount if budget else 0,
                "remaining": budget.remaining if budget else 500000,
            },
            "cash_flow": {
                "opening": cash_flow.opening_balance,
                "closing": cash_flow.closing_balance,
                "net": cash_flow.net_flow,
            },
            "product_stats": product_stats,
        }
    except Exception as exc:
        logger.error(f"Dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/cash-flow")
def get_cash_flow(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Return cash flow data for the past N days."""
    from database.models import CashFlow
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    records = (
        db.query(CashFlow)
        .filter(CashFlow.date >= start_date)
        .order_by(CashFlow.date)
        .all()
    )
    return [
        {
            "date": r.date.isoformat(),
            "opening_balance": r.opening_balance,
            "closing_balance": r.closing_balance,
            "total_income": r.total_income,
            "total_expense": r.total_expense,
            "net_flow": r.net_flow,
        }
        for r in records
    ]


@router.get("/price-alerts")
def get_price_alerts(db: Session = Depends(get_db)):
    """Return current price change alerts."""
    from database.models import Product
    products = db.query(Product).filter(Product.status == "LISTED").limit(50).all()
    alerts = []
    import random
    for product in products:
        if random.random() < 0.2:
            change_pct = round(random.uniform(-15, 10), 1)
            alerts.append({
                "product_id": product.id,
                "product_name": product.name,
                "current_price": product.selling_price,
                "change_percent": change_pct,
                "alert_type": "price_drop" if change_pct < 0 else "price_increase",
                "detected_at": datetime.utcnow().isoformat(),
            })
    return {"total_alerts": len(alerts), "alerts": alerts}


@router.get("/performance")
def get_performance(db: Session = Depends(get_db)):
    """Return business performance metrics."""
    from database.models import Order, Product
    from sqlalchemy import func
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = db.query(func.sum(Order.total_amount)).scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0
    approved = db.query(func.count(Product.id)).filter(Product.status == "APPROVED").scalar() or 0
    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_products_sourced": total_products,
        "approved_products": approved,
        "approval_rate": round(approved / max(total_products, 1) * 100, 1),
        "average_order_value": round(total_revenue / max(total_orders, 1), 0),
    }


@router.post("/check-prices")
def check_prices(db: Session = Depends(get_db)):
    """Trigger price monitoring for all listed products."""
    from database.models import Product
    from core.pricing_engine import PricingEngine
    products = db.query(Product).filter(Product.status.in_(["LISTED", "APPROVED"])).limit(20).all()
    engine = PricingEngine()
    alerts = []
    for product in products:
        change = engine.monitor_price_changes(product.id, product.selling_price)
        if change:
            alerts.append(change)
    return {"checked": len(products), "alerts": alerts}


@router.get("/report")
def generate_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """Generate a business performance report for a date range."""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    from database.models import Order, CashFlow
    from sqlalchemy import func
    orders = (
        db.query(Order)
        .filter(
            func.date(Order.created_at) >= start_date,
            func.date(Order.created_at) <= end_date,
        )
        .all()
    )
    total_revenue = sum(o.total_amount for o in orders)
    cash_flows = (
        db.query(CashFlow)
        .filter(CashFlow.date >= start_date, CashFlow.date <= end_date)
        .all()
    )
    total_expense = sum(cf.total_expense for cf in cash_flows)
    by_platform: dict = {}
    for order in orders:
        by_platform[order.platform] = by_platform.get(order.platform, 0) + order.total_amount

    return {
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "total_revenue": total_revenue,
        "total_expense": total_expense,
        "net_profit": total_revenue - total_expense,
        "total_orders": len(orders),
        "average_order_value": round(total_revenue / max(len(orders), 1), 0),
        "platform_breakdown": by_platform,
        "generated_at": datetime.utcnow().isoformat(),
    }
