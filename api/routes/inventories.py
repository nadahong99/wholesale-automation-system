from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Inventory
from api.schemas.inventory import Inventory as InventorySchema, InventoryCreate

router = APIRouter(prefix="/inventories", tags=["inventories"])

@router.post("/", response_model=InventorySchema)
def create_inventory(inventory: InventoryCreate, db: Session = Depends(get_db)):
    db_inventory = Inventory(stock_quantity=inventory.stock_quantity, product_id=inventory.product_id)
    db.add(db_inventory)
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

@router.get("/", response_model=list)
def get_inventories(db: Session = Depends(get_db)):
    return db.query(Inventory).all()

@router.get("/{inventory_id}", response_model=InventorySchema)
def get_inventory(inventory_id: int, db: Session = Depends(get_db)):
    return db.query(Inventory).filter(Inventory.id == inventory_id).first()

@router.put("/{inventory_id}", response_model=InventorySchema)
def update_inventory(inventory_id: int, inventory: InventoryCreate, db: Session = Depends(get_db)):
    db_inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    db_inventory.stock_quantity = inventory.stock_quantity
    db_inventory.product_id = inventory.product_id
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

@router.delete("/{inventory_id}")
def delete_inventory(inventory_id: int, db: Session = Depends(get_db)):
    db_inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    db.delete(db_inventory)
    db.commit()
    return {"message": "Inventory deleted"}