import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """Tracks and analyzes business performance metrics."""

    def __init__(self, db_session=None):
        self.db = db_session

    def track_sourcing_performance(self, result) -> Dict:
        """Record sourcing run metrics."""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_scraped": result.total_scraped,
            "golden_matches": result.golden_keyword_matches,
            "auto_list": result.auto_list_count,
            "bundle": result.bundle_count,
            "ceo_review": result.ceo_review_count,
            "below_margin": result.below_margin_count,
            "total_actionable": result.total_actionable,
            "success_rate": round(
                result.total_actionable / max(result.total_scraped, 1) * 100, 2
            ),
        }
        logger.info(
            f"Sourcing performance: scraped={result.total_scraped} "
            f"actionable={result.total_actionable} "
            f"rate={metrics['success_rate']:.1f}%"
        )
        return metrics

    def track_order_performance(self, order: Dict) -> Dict:
        """Record order metrics."""
        metrics = {
            "order_id": order.get("id") or order.get("order_id"),
            "platform": order.get("platform"),
            "amount": order.get("total_amount", 0),
            "status": order.get("status"),
            "tracked_at": datetime.utcnow().isoformat(),
        }
        logger.info(
            f"Order tracked: id={metrics['order_id']} "
            f"platform={metrics['platform']} amount={metrics['amount']:,}"
        )
        return metrics

    def get_conversion_rate(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> float:
        """Return ratio of delivered orders to total orders."""
        if not self.db:
            return 0.0
        from database.models import Order
        from sqlalchemy import func
        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=30))
        total = (
            self.db.query(func.count(Order.id))
            .filter(
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date,
            )
            .scalar() or 0
        )
        delivered = (
            self.db.query(func.count(Order.id))
            .filter(
                func.date(Order.created_at) >= start_date,
                func.date(Order.created_at) <= end_date,
                Order.status.in_(["DELIVERED", "CONFIRMED"]),
            )
            .scalar() or 0
        )
        return round(delivered / max(total, 1) * 100, 2)

    def get_top_products(self, limit: int = 10) -> List[Dict]:
        """Return top performing products by total sales."""
        if not self.db:
            return []
        from database.models import Order, Product
        from sqlalchemy import func
        results = (
            self.db.query(
                Order.product_id,
                func.sum(Order.total_amount).label("total_sales"),
                func.count(Order.id).label("order_count"),
            )
            .filter(Order.product_id.isnot(None))
            .group_by(Order.product_id)
            .order_by(func.sum(Order.total_amount).desc())
            .limit(limit)
            .all()
        )
        top_products = []
        for r in results:
            product = self.db.query(Product).filter(Product.id == r.product_id).first()
            top_products.append({
                "product_id": r.product_id,
                "name": product.name if product else "Unknown",
                "total_sales": int(r.total_sales),
                "order_count": r.order_count,
                "platform": product.platform if product else "unknown",
            })
        return top_products

    def get_platform_performance(self) -> Dict:
        """Compare performance metrics between Naver and Coupang."""
        if not self.db:
            return {"naver": {}, "coupang": {}}
        from database.models import Order
        from sqlalchemy import func
        result = {}
        for platform in ["naver", "coupang"]:
            revenue = (
                self.db.query(func.sum(Order.total_amount))
                .filter(Order.platform == platform)
                .scalar() or 0
            )
            count = (
                self.db.query(func.count(Order.id))
                .filter(Order.platform == platform)
                .scalar() or 0
            )
            result[platform] = {
                "total_revenue": int(revenue),
                "order_count": count,
                "avg_order_value": int(revenue / max(count, 1)),
            }
        return result

    def calculate_roi(self) -> Dict:
        """Calculate overall return on investment."""
        if not self.db:
            return {"roi_percent": 0.0, "total_invested": 0, "total_returned": 0}
        from database.models import Order, Transaction
        from sqlalchemy import func
        total_revenue = (
            self.db.query(func.sum(Order.total_amount))
            .filter(Order.status.in_(["DELIVERED", "CONFIRMED"]))
            .scalar() or 0
        )
        total_expense = (
            self.db.query(func.sum(Transaction.amount))
            .filter(Transaction.type == "expense")
            .scalar() or 0
        )
        roi = (
            (total_revenue - total_expense) / max(total_expense, 1) * 100
        )
        return {
            "total_revenue": int(total_revenue),
            "total_expense": int(total_expense),
            "net_profit": int(total_revenue - total_expense),
            "roi_percent": round(roi, 2),
        }

    def generate_performance_report(self, period: str = "daily") -> Dict:
        """Generate a performance report for daily, weekly, or monthly periods."""
        end_date = date.today()
        if period == "daily":
            start_date = end_date
        elif period == "weekly":
            start_date = end_date - timedelta(days=7)
        elif period == "monthly":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=30)

        conversion_rate = self.get_conversion_rate(start_date, end_date)
        top_products = self.get_top_products(5)
        platform_perf = self.get_platform_performance()
        roi = self.calculate_roi()

        return {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "conversion_rate": conversion_rate,
            "top_products": top_products,
            "platform_performance": platform_perf,
            "roi": roi,
            "generated_at": datetime.utcnow().isoformat(),
        }
