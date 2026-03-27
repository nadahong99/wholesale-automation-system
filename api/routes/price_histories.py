from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import PriceHistory
from api.schemas.price_history import PriceHistoryCreate, PriceHistoryResponse

router = APIRouter(prefix="/price-histories", tags=["price_histories"])


@router.get("/", response_model=List[PriceHistoryResponse])
def get_price_histories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(PriceHistory).offset(skip).limit(limit).all()


@router.get("/{price_history_id}", response_model=PriceHistoryResponse)
def get_price_history(price_history_id: int, db: Session = Depends(get_db)):
    price_history = db.query(PriceHistory).filter(PriceHistory.id == price_history_id).first()
    if not price_history:
        raise HTTPException(status_code=404, detail="PriceHistory not found")
    return price_history


@router.post("/", response_model=PriceHistoryResponse, status_code=201)
def create_price_history(price_history: PriceHistoryCreate, db: Session = Depends(get_db)):
    db_price_history = PriceHistory(**price_history.model_dump())
    db.add(db_price_history)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not create price history record")
    db.refresh(db_price_history)
    return db_price_history


@router.delete("/{price_history_id}", status_code=204)
def delete_price_history(price_history_id: int, db: Session = Depends(get_db)):
    db_price_history = db.query(PriceHistory).filter(PriceHistory.id == price_history_id).first()
    if not db_price_history:
        raise HTTPException(status_code=404, detail="PriceHistory not found")
    db.delete(db_price_history)
    db.commit()
