# api/routes/monitoring.py
"""REST endpoints for monitoring & budget."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.session import get_db
from database import crud, schemas
from api.models import BudgetSetRequest, PriceMonitorResponse
from monitoring.cash_flow_monitor import get_cash_flow_summary
from utils.logger import get_logger

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
logger = get_logger("api.monitoring")


@router.post("/price-monitor", response_model=PriceMonitorResponse)
def trigger_price_monitor():
    """Manually trigger a price monitoring run."""
    from monitoring.price_monitor import run_price_monitoring

    adjusted = run_price_monitoring()
    return PriceMonitorResponse(
        adjusted=adjusted,
        message=f"{adjusted} products price-adjusted.",
    )


@router.get("/cash-flow")
def cash_flow(db: Session = Depends(get_db)):
    """Return today's cash flow summary."""
    return get_cash_flow_summary(db)


@router.post("/budget")
def set_budget(req: BudgetSetRequest, db: Session = Depends(get_db)):
    """Set the daily budget."""
    budget = crud.set_daily_budget(db, req.amount, set_by=req.set_by)
    return schemas.BudgetRead.model_validate(budget)


@router.get("/budget")
def get_budget(db: Session = Depends(get_db)):
    """Return current daily budget."""
    budget = crud.get_or_create_budget(db)
    return schemas.BudgetRead.model_validate(budget)
