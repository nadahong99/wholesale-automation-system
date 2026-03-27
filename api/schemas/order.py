from pydantic import BaseModel

class OrderBase(BaseModel):
    quantity: int
    order_date: str

class OrderCreate(OrderBase):
    product_id: int

class Order(OrderBase):
    id: int
    product_id: int

    class Config:
        from_attributes = True