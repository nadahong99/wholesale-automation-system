import logging
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import Budget, CashFlow, KeywordStat, Order, Product, Transaction
from database.schemas import (
    BudgetCreate, OrderCreate, ProductCreate, ProductUpdate, TransactionCreate
)

logger = logging.getLogger(__name__)


# ── Product CRUD ──────────────────────────────────────────────────────────────

def create_product(db: Session, data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    logger.info(f"Created product id={product.id} name={product.name!r}")
    return product


def get_product(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()


def get_products(
    db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None
) -> List[Product]:
    q = db.query(Product)
    if status:
        q = q.filter(Product.status == status)
    return q.offset(skip).limit(limit).all()


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Optional[Product]:
    product = get_product(db, product_id)
    if not product:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> bool:
    product = get_product(db, product_id)
    if not product:
        return False
    db.delete(product)
    db.commit()
    return True


def get_products_by_margin(db: Session, min_margin: float = 20.0) -> List[Product]:
    return (
        db.query(Product)
        .filter(Product.margin_percent >= min_margin)
        .order_by(Product.margin_percent.desc())
        .all()
    )


# ── Order CRUD ────────────────────────────────────────────────────────────────

def create_order(db: Session, data: OrderCreate) -> Order:
    order = Order(**data.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    logger.info(f"Created order id={order.id} order_number={order.order_number!r}")
    return order


def get_order(db: Session, order_id: int) -> Optional[Order]:
    return db.query(Order).filter(Order.id == order_id).first()


def get_orders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    platform: Optional[str] = None,
) -> List[Order]:
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if platform:
        q = q.filter(Order.platform == platform)
    return q.offset(skip).limit(limit).all()


def update_order_status(db: Session, order_id: int, status: str) -> Optional[Order]:
    order = get_order(db, order_id)
    if not order:
        return None
    order.status = status
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order


def get_todays_orders(db: Session) -> List[Order]:
    today = date.today()
    return (
        db.query(Order)
        .filter(func.date(Order.created_at) == today)
        .all()
    )


def calculate_daily_profit(db: Session, target_date: Optional[date] = None) -> int:
    target_date = target_date or date.today()
    orders = (
        db.query(Order)
        .filter(
            func.date(Order.created_at) == target_date,
            Order.status.in_(["DELIVERED", "CONFIRMED"]),
        )
        .all()
    )
    return sum(o.total_amount for o in orders)


# ── Transaction CRUD ──────────────────────────────────────────────────────────

def create_transaction(db: Session, data: TransactionCreate) -> Transaction:
    tx = Transaction(**data.model_dump())
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def get_transaction(db: Session, tx_id: int) -> Optional[Transaction]:
    return db.query(Transaction).filter(Transaction.id == tx_id).first()


def get_transactions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    tx_type: Optional[str] = None,
) -> List[Transaction]:
    q = db.query(Transaction)
    if tx_type:
        q = q.filter(Transaction.type == tx_type)
    return q.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()


# ── Budget CRUD ───────────────────────────────────────────────────────────────

def create_or_get_budget(db: Session, target_date: date, daily_budget: int = 500000) -> Budget:
    budget = db.query(Budget).filter(Budget.date == target_date).first()
    if budget:
        return budget
    budget = Budget(
        date=target_date,
        daily_budget=daily_budget,
        spent_amount=0,
        remaining=daily_budget,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def get_budget_status(db: Session, target_date: Optional[date] = None) -> Optional[Budget]:
    target_date = target_date or date.today()
    return db.query(Budget).filter(Budget.date == target_date).first()


def update_budget_spent(db: Session, target_date: date, additional_spent: int) -> Optional[Budget]:
    budget = db.query(Budget).filter(Budget.date == target_date).first()
    if not budget:
        return None
    budget.spent_amount += additional_spent
    budget.remaining = budget.daily_budget - budget.spent_amount
    db.commit()
    db.refresh(budget)
    return budget


# ── CashFlow CRUD ─────────────────────────────────────────────────────────────

def get_or_create_cash_flow(db: Session, target_date: date, opening_balance: int = 0) -> CashFlow:
    cf = db.query(CashFlow).filter(CashFlow.date == target_date).first()
    if cf:
        return cf
    cf = CashFlow(
        date=target_date,
        opening_balance=opening_balance,
        closing_balance=opening_balance,
        total_income=0,
        total_expense=0,
        net_flow=0,
    )
    db.add(cf)
    db.commit()
    db.refresh(cf)
    return cf


def update_cash_flow(
    db: Session, target_date: date, income: int = 0, expense: int = 0
) -> Optional[CashFlow]:
    cf = db.query(CashFlow).filter(CashFlow.date == target_date).first()
    if not cf:
        return None
    cf.total_income += income
    cf.total_expense += expense
    cf.net_flow = cf.total_income - cf.total_expense
    cf.closing_balance = cf.opening_balance + cf.net_flow
    db.commit()
    db.refresh(cf)
    return cf


# ── KeywordStat CRUD ──────────────────────────────────────────────────────────

def create_or_update_keyword(
    db: Session, keyword: str, search_volume: int, product_count: int, golden_ratio: float = 10.0
) -> KeywordStat:
    ratio = search_volume / max(product_count, 1)
    stat = db.query(KeywordStat).filter(KeywordStat.keyword == keyword).first()
    if stat:
        stat.search_volume = search_volume
        stat.product_count = product_count
        stat.ratio = ratio
        stat.is_golden = ratio >= golden_ratio
        stat.checked_at = datetime.utcnow()
    else:
        stat = KeywordStat(
            keyword=keyword,
            search_volume=search_volume,
            product_count=product_count,
            ratio=ratio,
            is_golden=ratio >= golden_ratio,
        )
        db.add(stat)
    db.commit()
    db.refresh(stat)
    return stat


def get_golden_keywords(db: Session) -> List[KeywordStat]:
    return db.query(KeywordStat).filter(KeywordStat.is_golden == True).all()
