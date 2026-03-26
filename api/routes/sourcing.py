import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.session import get_db
from database.crud import get_products, get_product, update_product, get_golden_keywords
from database.schemas import ProductResponse, ProductUpdate
from api.models import SourcingRequest, SourcingResponse

router = APIRouter(prefix="/sourcing", tags=["sourcing"])
logger = logging.getLogger(__name__)


@router.post("/run", response_model=SourcingResponse)
def run_sourcing(request: SourcingRequest, db: Session = Depends(get_db)):
    """Trigger a full sourcing cycle across all wholesalers."""
    try:
        from core.sourcing_engine import SourcingEngine
        engine = SourcingEngine(db_session=db, min_margin=request.min_margin_percent)
        result = engine.run_full_sourcing()
        return SourcingResponse(
            total_scraped=result.total_scraped,
            golden_keyword_matches=result.golden_keyword_matches,
            auto_list_count=result.auto_list_count,
            bundle_count=result.bundle_count,
            ceo_review_count=result.ceo_review_count,
            below_margin_count=result.below_margin_count,
            total_actionable=result.total_actionable,
            errors=result.errors,
        )
    except Exception as exc:
        logger.error(f"Sourcing run failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/products", response_model=List[ProductResponse])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List sourced products with optional status filter."""
    return get_products(db, skip=skip, limit=limit, status=status)


@router.get("/keywords")
def get_keywords(db: Session = Depends(get_db)):
    """Return all golden keywords with their statistics."""
    keywords = get_golden_keywords(db)
    return [
        {
            "keyword": k.keyword,
            "search_volume": k.search_volume,
            "product_count": k.product_count,
            "ratio": k.ratio,
            "is_golden": k.is_golden,
        }
        for k in keywords
    ]


@router.post("/approve/{product_id}", response_model=ProductResponse)
def approve_product(product_id: int, db: Session = Depends(get_db)):
    """Approve a product for listing."""
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    updated = update_product(db, product_id, ProductUpdate(status="APPROVED"))
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update product status")
    logger.info(f"Product {product_id} approved")
    return updated


@router.post("/reject/{product_id}", response_model=ProductResponse)
def reject_product(product_id: int, db: Session = Depends(get_db)):
    """Reject a sourced product."""
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    updated = update_product(db, product_id, ProductUpdate(status="REJECTED"))
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update product status")
    logger.info(f"Product {product_id} rejected")
    return updated


@router.get("/stats")
def get_sourcing_stats(db: Session = Depends(get_db)):
    """Return aggregate sourcing statistics."""
    from sqlalchemy import func
    from database.models import Product
    stats = (
        db.query(Product.status, func.count(Product.id))
        .group_by(Product.status)
        .all()
    )
    result = {status: count for status, count in stats}
    total = sum(result.values())
    return {
        "total_products": total,
        "by_status": result,
        "approved_count": result.get("APPROVED", 0),
        "pending_count": result.get("PENDING_APPROVAL", 0),
        "rejected_count": result.get("REJECTED", 0),
    }
