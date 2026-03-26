# api/routes/sourcing.py
"""REST endpoints for sourcing & keyword filtering."""
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from database.session import get_db
from api.models import SourcingTriggerRequest, SourcingTriggerResponse, GoldenKeywordFilterResponse
from utils.logger import get_logger

router = APIRouter(prefix="/sourcing", tags=["sourcing"])
logger = get_logger("api.sourcing")


@router.post("/trigger", response_model=SourcingTriggerResponse)
def trigger_sourcing(
    req: SourcingTriggerRequest,
    background_tasks: BackgroundTasks,
):
    """Manually trigger a sourcing run (runs in background)."""
    from core.sourcing_engine import run_sourcing

    background_tasks.add_task(run_sourcing, req.target_per_wholesaler)
    return SourcingTriggerResponse(
        total_products=0,
        message="Sourcing task started in background.",
    )


@router.post("/golden-keyword", response_model=GoldenKeywordFilterResponse)
def trigger_golden_keyword(background_tasks: BackgroundTasks):
    """Manually trigger the golden keyword filter."""
    from scheduler.tasks import golden_keyword_filter

    background_tasks.add_task(golden_keyword_filter.delay)
    return GoldenKeywordFilterResponse(
        sent_to_ceo=0,
        message="Golden keyword filter started in background.",
    )
