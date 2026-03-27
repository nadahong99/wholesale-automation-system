from pydantic import BaseModel

class PriceHistoryBase(BaseModel):
    price: float
    date_recorded: str

class PriceHistoryCreate(PriceHistoryBase):
    product_id: int

class PriceHistory(PriceHistoryBase):
    id: int
    product_id: int

    class Config:
        from_attributes = True