from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Date
)
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False)
    purchase_price = Column(Integer, nullable=False)
    selling_price = Column(Integer, nullable=False)
    platform = Column(String(50), nullable=False, default="naver")
    url = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    moq = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default="SOURCED")
    keyword = Column(String(200), nullable=True)
    wholesaler = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    margin_percent = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("Order", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r} price={self.selling_price}>"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    platform = Column(String(50), nullable=False)
    order_number = Column(String(200), unique=True, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Integer, nullable=False)
    total_amount = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="orders")
    transactions = relationship("Transaction", back_populates="order")

    def __repr__(self) -> str:
        return f"<Order id={self.id} order_number={self.order_number!r} status={self.status}>"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    type = Column(String(20), nullable=False)  # income / expense
    amount = Column(Integer, nullable=False)
    description = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} type={self.type} amount={self.amount}>"


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    daily_budget = Column(Integer, nullable=False, default=500000)
    spent_amount = Column(Integer, nullable=False, default=0)
    remaining = Column(Integer, nullable=False, default=500000)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Budget date={self.date} budget={self.daily_budget} remaining={self.remaining}>"


class CashFlow(Base):
    __tablename__ = "cash_flows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True)
    opening_balance = Column(Integer, nullable=False, default=0)
    closing_balance = Column(Integer, nullable=False, default=0)
    total_income = Column(Integer, nullable=False, default=0)
    total_expense = Column(Integer, nullable=False, default=0)
    net_flow = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<CashFlow date={self.date} net_flow={self.net_flow}>"


class KeywordStat(Base):
    __tablename__ = "keyword_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(200), nullable=False)
    search_volume = Column(Integer, nullable=False, default=0)
    product_count = Column(Integer, nullable=False, default=1)
    ratio = Column(Float, nullable=False, default=0.0)
    is_golden = Column(Boolean, nullable=False, default=False)
    checked_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<KeywordStat keyword={self.keyword!r} ratio={self.ratio} golden={self.is_golden}>"
