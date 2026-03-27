from pydantic import BaseModel

class ProductBase(BaseModel):
    name: str
    sourcing_link: str

class ProductCreate(ProductBase):
    supplier_id: int

class Product(ProductBase):
    id: int
    supplier_id: int

    class Config:
        from_attributes = True