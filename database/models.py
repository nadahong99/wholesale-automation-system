from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Supplier(Base):
    __tablename__ = 'suppliers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact_info = Column(String)

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    sourcing_link = Column(String, nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    supplier = relationship('Supplier', back_populates='products')

class PriceHistory(Base):
    __tablename__ = 'price_history'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    price = Column(Float, nullable=False)
    date_recorded = Column(String, nullable=False)
    product = relationship('Product', back_populates='price_history')

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer, nullable=False)
    order_date = Column(String, nullable=False)
    product = relationship('Product', back_populates='orders')

class Inventory(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    stock_quantity = Column(Integer, nullable=False)
    product = relationship('Product', back_populates='inventory')

Supplier.products = relationship('Product', order_by=Product.id, back_populates='supplier')
Product.price_history = relationship('PriceHistory', order_by=PriceHistory.id, back_populates='product')
Product.orders = relationship('Order', order_by=Order.id, back_populates='product')
Product.inventory = relationship('Inventory', order_by=Inventory.id, back_populates='product')
