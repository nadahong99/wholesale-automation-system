from pydantic import BaseModel

class InventoryBase(BaseModel):
    stock_quantity: int

class InventoryCreate(InventoryBase):
    product_id: int

class Inventory(InventoryBase):
    id: int
    product_id: int

    class Config:
        from_attributes = True