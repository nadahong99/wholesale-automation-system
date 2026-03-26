# database/models.py
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Date,
)
from sqlalchemy.orm import relationship
from database.session import Base


class Wholesaler(Base):
    __tablename__ = "wholesalers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    base_url = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    products = relationship("Product", back_populates="wholesaler")
    orders = relationship("Order", back_populates="wholesaler")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    category = Column(String(100))
    wholesale_price = Column(Float, nullable=False)
    suggested_selling_price = Column(Float)
    actual_selling_price = Column(Float)
    moq = Column(Integer, default=1)
    image_url = Column(String(1000))
    gcs_image_url = Column(String(1000))
    description = Column(Text)
    wholesaler_id = Column(Integer, ForeignKey("wholesalers.id"))
    external_product_id = Column(String(200))
    naver_product_id = Column(String(200))
    coupang_product_id = Column(String(200))
    is_active = Column(Boolean, default=True)
    is_listed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    wholesaler = relationship("Wholesaler", back_populates="products")
    daily_products = relationship("DailyProduct", back_populates="product")
    orders = relationship("Order", back_populates="product")
    price_history = relationship("PriceHistory", back_populates="product")


class DailyProduct(Base):
    __tablename__ = "daily_products"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, default=lambda: datetime.utcnow().date())
    product_id = Column(Integer, ForeignKey("products.id"))
    search_volume = Column(Integer, default=0)
    product_count_in_market = Column(Integer, default=0)
    golden_keyword_score = Column(Float, default=0.0)
    approved_by_ceo = Column(String(20), default="pending")  # pending / approved / rejected
    approved_at = Column(DateTime)
    sent_to_ceo_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="daily_products")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    customer_order_id = Column(String(200))
    wholesale_order_id = Column(String(200))
    quantity = Column(Integer, default=1)
    wholesaler_id = Column(Integer, ForeignKey("wholesalers.id"))
    status = Column(String(50), default="pending")
    unit_price = Column(Float)
    total_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    product = relationship("Product", back_populates="orders")
    wholesaler = relationship("Wholesaler", back_populates="orders")


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, default=lambda: datetime.utcnow().date(), unique=True)
    total_sales = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    margin_percent = Column(Float, default=0.0)
    cash_available = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    new_products_sourced = Column(Integer, default=0)
    products_approved = Column(Integer, default=0)
    warning_flags = Column(Text)  # JSON-serialized list of warning strings
    created_at = Column(DateTime, default=datetime.utcnow)


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    date = Column(DateTime, default=datetime.utcnow)
    competitor_price = Column(Float)
    our_price = Column(Float)
    margin_percent = Column(Float)
    platform = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="price_history")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, default=lambda: datetime.utcnow().date())
    daily_budget = Column(Float, default=1000000.0)
    spent = Column(Float, default=0.0)
    remaining = Column(Float, default=1000000.0)
    set_by = Column(String(100), default="system")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
