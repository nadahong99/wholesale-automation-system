from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# BigInteger that falls back to Integer on SQLite (which does not support BIGINT AUTOINCREMENT)
_BigIntPK = BigInteger().with_variant(Integer, "sqlite")

from .connection import Base


class Supplier(Base):
    """도매처(공급업체) 모델"""

    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    contact_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="supplier", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Supplier id={self.id} name={self.name!r}>"


class Product(Base):
    """상품 모델"""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, index=True)
    supplier_id: Mapped[int] = mapped_column(
        _BigIntPK, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="products")
    price_histories: Mapped[List["PriceHistory"]] = relationship(
        "PriceHistory", back_populates="product", cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="product", cascade="all, delete-orphan"
    )
    inventories: Mapped[List["Inventory"]] = relationship(
        "Inventory", back_populates="product", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r} sku={self.sku!r}>"


class PriceHistory(Base):
    """가격 히스토리 모델"""

    __tablename__ = "price_histories"

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        _BigIntPK, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    old_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    new_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    change_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product: Mapped["Product"] = relationship("Product", back_populates="price_histories")

    def __repr__(self) -> str:
        return (
            f"<PriceHistory id={self.id} product_id={self.product_id} "
            f"old={self.old_price} new={self.new_price}>"
        )


class Order(Base):
    """주문 모델"""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    product_id: Mapped[int] = mapped_column(
        _BigIntPK, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    delivery_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    product: Mapped["Product"] = relationship("Product", back_populates="orders")

    def __repr__(self) -> str:
        return f"<Order id={self.id} order_number={self.order_number!r} status={self.status!r}>"


class Inventory(Base):
    """재고 모델"""

    __tablename__ = "inventories"

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        _BigIntPK, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    warehouse_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_checked: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    product: Mapped["Product"] = relationship("Product", back_populates="inventories")

    def __repr__(self) -> str:
        return (
            f"<Inventory id={self.id} product_id={self.product_id} "
            f"quantity={self.quantity}>"
        )
