# monitoring/performance_tracker.py
"""Track and compute sales performance metrics."""
from datetime import datetime, date, timedelta
from typing import Dict, List
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from database.session import SessionLocal
from database import models
from utils.logger import get_logger

logger = get_logger("performance_tracker")


def get_top_products(db: Session, limit: int = 5, for_date: date = None) -> List[Dict]:
    """Return top-*limit* selling products for *for_date* (defaults to today)."""
    if for_date is None:
        for_date = datetime.utcnow().date()

    results = (
        db.query(
            models.Product.id,
            models.Product.name,
            func.count(models.Order.id).label("order_count"),
            func.sum(models.Order.total_price).label("revenue"),
        )
        .join(models.Order, models.Order.product_id == models.Product.id)
        .filter(func.date(models.Order.created_at) == for_date)
        .group_by(models.Product.id, models.Product.name)
        .order_by(desc("revenue"))
        .limit(limit)
        .all()
    )

    return [
        {
            "product_id": row.id,
            "product_name": row.name,
            "order_count": row.order_count,
            "revenue": float(row.revenue or 0),
        }
        for row in results
    ]


def compute_daily_metrics(db: Session, for_date: date = None) -> Dict:
    """Compute and return aggregated daily sales metrics."""
    if for_date is None:
        for_date = datetime.utcnow().date()

    orders = (
        db.query(models.Order)
        .filter(func.date(models.Order.created_at) == for_date)
        .all()
    )

    total_revenue = sum(o.total_price or 0 for o in orders)
    total_cost = sum((o.unit_price or 0) * (o.quantity or 1) for o in orders)
    total_profit = total_revenue - total_cost
    margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0

    return {
        "date": str(for_date),
        "total_orders": len(orders),
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "margin_percent": margin,
    }


def get_weekly_summary(db: Session) -> List[Dict]:
    """Return daily metrics for the past 7 days."""
    summaries = []
    today = datetime.utcnow().date()
    for i in range(7):
        d = today - timedelta(days=i)
        summaries.append(compute_daily_metrics(db, d))
    return summaries
