# database/crud.py
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from database import models
from database.schemas import (
    ProductCreate,
    ProductUpdate,
    OrderCreate,
    OrderUpdate,
    DailyProductCreate,
)
from utils.logger import get_logger

logger = get_logger("crud")


# ─── Wholesaler ──────────────────────────────────────────────────────────────

def get_or_create_wholesaler(db: Session, name: str, base_url: str = "") -> models.Wholesaler:
    obj = db.query(models.Wholesaler).filter(models.Wholesaler.name == name).first()
    if obj:
        return obj
    obj = models.Wholesaler(name=name, base_url=base_url)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ─── Product ─────────────────────────────────────────────────────────────────

def create_product(db: Session, product: ProductCreate) -> models.Product:
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
) -> List[models.Product]:
    q = db.query(models.Product)
    if active_only:
        q = q.filter(models.Product.is_active == True)
    return q.offset(skip).limit(limit).all()


def get_listed_products(db: Session) -> List[models.Product]:
    return (
        db.query(models.Product)
        .filter(and_(models.Product.is_listed == True, models.Product.is_active == True))
        .all()
    )


def update_product(db: Session, product_id: int, update: ProductUpdate) -> Optional[models.Product]:
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(db_product, field, value)
    db.commit()
    db.refresh(db_product)
    return db_product


# ─── DailyProduct ────────────────────────────────────────────────────────────

def create_daily_product(db: Session, dp: DailyProductCreate) -> models.DailyProduct:
    db_dp = models.DailyProduct(**dp.model_dump())
    db.add(db_dp)
    db.commit()
    db.refresh(db_dp)
    return db_dp


def get_daily_products_for_date(
    db: Session, target_date: date, approved_only: bool = False
) -> List[models.DailyProduct]:
    q = db.query(models.DailyProduct).filter(models.DailyProduct.date == target_date)
    if approved_only:
        q = q.filter(models.DailyProduct.approved_by_ceo == "approved")
    return q.order_by(desc(models.DailyProduct.golden_keyword_score)).all()


def approve_daily_product(db: Session, daily_product_id: int) -> Optional[models.DailyProduct]:
    dp = db.query(models.DailyProduct).filter(models.DailyProduct.id == daily_product_id).first()
    if not dp:
        return None
    dp.approved_by_ceo = "approved"
    dp.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(dp)
    return dp


def reject_daily_product(db: Session, daily_product_id: int) -> Optional[models.DailyProduct]:
    dp = db.query(models.DailyProduct).filter(models.DailyProduct.id == daily_product_id).first()
    if not dp:
        return None
    dp.approved_by_ceo = "rejected"
    dp.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(dp)
    return dp


# ─── Order ───────────────────────────────────────────────────────────────────

def create_order(db: Session, order: OrderCreate) -> models.Order:
    db_order = models.Order(**order.model_dump())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


def get_order(db: Session, order_id: int) -> Optional[models.Order]:
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def update_order(db: Session, order_id: int, update: OrderUpdate) -> Optional[models.Order]:
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(db_order, field, value)
    db.commit()
    db.refresh(db_order)
    return db_order


# ─── DailyReport ─────────────────────────────────────────────────────────────

def get_or_create_daily_report(db: Session, report_date: date) -> models.DailyReport:
    obj = db.query(models.DailyReport).filter(models.DailyReport.date == report_date).first()
    if obj:
        return obj
    obj = models.DailyReport(date=report_date)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def save_daily_report(db: Session, report: models.DailyReport) -> models.DailyReport:
    db.commit()
    db.refresh(report)
    return report


# ─── PriceHistory ────────────────────────────────────────────────────────────

def add_price_history(
    db: Session,
    product_id: int,
    competitor_price: float,
    our_price: float,
    margin_percent: float,
    platform: str,
) -> models.PriceHistory:
    obj = models.PriceHistory(
        product_id=product_id,
        competitor_price=competitor_price,
        our_price=our_price,
        margin_percent=margin_percent,
        platform=platform,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_price_history(
    db: Session,
    product_id: int,
    limit: int = 100,
) -> List[models.PriceHistory]:
    return (
        db.query(models.PriceHistory)
        .filter(models.PriceHistory.product_id == product_id)
        .order_by(desc(models.PriceHistory.date))
        .limit(limit)
        .all()
    )


# ─── Budget ──────────────────────────────────────────────────────────────────

def get_today_budget(db: Session) -> Optional[models.Budget]:
    today = datetime.utcnow().date()
    return db.query(models.Budget).filter(models.Budget.date == today).first()


def get_or_create_budget(db: Session, daily_amount: float = 1_000_000.0) -> models.Budget:
    today = datetime.utcnow().date()
    obj = db.query(models.Budget).filter(models.Budget.date == today).first()
    if obj:
        return obj
    obj = models.Budget(date=today, daily_budget=daily_amount, remaining=daily_amount)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def deduct_budget(db: Session, amount: float) -> models.Budget:
    budget = get_or_create_budget(db)
    budget.spent += amount
    budget.remaining -= amount
    db.commit()
    db.refresh(budget)
    return budget


def set_daily_budget(db: Session, amount: float, set_by: str = "CEO") -> models.Budget:
    budget = get_or_create_budget(db, daily_amount=amount)
    budget.daily_budget = amount
    budget.remaining = amount - budget.spent
    budget.set_by = set_by
    db.commit()
    db.refresh(budget)
    return budget
