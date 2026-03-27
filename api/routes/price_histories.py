from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import PriceHistory
from api.schemas.price_history import PriceHistory as PriceHistorySchema, PriceHistoryCreate

router = APIRouter(prefix="/price-histories", tags=["price_histories"])

@router.post("/", response_model=PriceHistorySchema)
def create_price_history(price_history: PriceHistoryCreate, db: Session = Depends(get_db)):
    db_price_history = PriceHistory(price=price_history.price, date_recorded=price_history.date_recorded, product_id=price_history.product_id)
    db.add(db_price_history)
    db.commit()
    db.refresh(db_price_history)
    return db_price_history

@router.get("/", response_model=list)
def get_price_histories(db: Session = Depends(get_db)):
    return db.query(PriceHistory).all()

@router.get("/{price_history_id}", response_model=PriceHistorySchema)
def get_price_history(price_history_id: int, db: Session = Depends(get_db)):
    return db.query(PriceHistory).filter(PriceHistory.id == price_history_id).first()

@router.put("/{price_history_id}", response_model=PriceHistorySchema)
def update_price_history(price_history_id: int, price_history: PriceHistoryCreate, db: Session = Depends(get_db)):
    db_price_history = db.query(PriceHistory).filter(PriceHistory.id == price_history_id).first()
    db_price_history.price = price_history.price
    db_price_history.date_recorded = price_history.date_recorded
    db_price_history.product_id = price_history.product_id
    db.commit()
    db.refresh(db_price_history)
    return db_price_history

@router.delete("/{price_history_id}")
def delete_price_history(price_history_id: int, db: Session = Depends(get_db)):
    db_price_history = db.query(PriceHistory).filter(PriceHistory.id == price_history_id).first()
    db.delete(db_price_history)
    db.commit()
    return {"message": "Price history deleted"}