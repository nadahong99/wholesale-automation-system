from pydantic import BaseModel

class SupplierBase(BaseModel):
    name: str
    contact_info: str = None

class SupplierCreate(SupplierBase):
    pass

class Supplier(SupplierBase):
    id: int

    class Config:
        from_attributes = True