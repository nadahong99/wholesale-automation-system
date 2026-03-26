# core/sourcing_engine.py
"""Daily product sourcing orchestrator – scrapes all 6 wholesalers."""
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from database.session import SessionLocal
from database import crud, models
from database.schemas import ProductCreate, DailyProductCreate
from integrations.wholesalers import (
    DaemaetopiaClient,
    EasymarketClient,
    DaemaepartnerClient,
    SinsangClient,
    MurraykoreaClient,
    DalgolmartClient,
)
from integrations.wholesalers.base import RawProduct
from integrations.gcs_upload import upload_bytes
from core.margin_calculator import MarginCalculator
from config.settings import settings
from config.constants import WHOLESALER_URLS
from utils.logger import get_logger
from utils.decorators import log_execution_time

logger = get_logger("sourcing_engine")

CLIENTS = [
    DaemaetopiaClient,
    EasymarketClient,
    DaemaepartnerClient,
    SinsangClient,
    MurraykoreaClient,
    DalgolmartClient,
]


def _download_image(url: str) -> Optional[bytes]:
    if not url:
        return None
    try:
        import requests
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.content
    except Exception as exc:
        logger.warning(f"Image download failed for {url}: {exc}")
        return None


def _save_raw_product(
    db: Session,
    raw: RawProduct,
    wholesaler: models.Wholesaler,
    calc: MarginCalculator,
) -> Optional[models.Product]:
    """Persist a RawProduct to the database, uploading image to GCS if possible."""
    try:
        gcs_url = None
        image_bytes = _download_image(raw.image_url)
        if image_bytes:
            gcs_url = upload_bytes(image_bytes)

        selling_price = calc.compute_selling_price(raw.wholesale_price)

        product = crud.create_product(
            db,
            ProductCreate(
                name=raw.name,
                category=raw.category,
                wholesale_price=raw.wholesale_price,
                suggested_selling_price=float(selling_price),
                moq=raw.moq,
                image_url=raw.image_url,
                gcs_image_url=gcs_url,
                description=raw.description,
                wholesaler_id=wholesaler.id,
                external_product_id=raw.external_product_id,
            ),
        )
        return product
    except Exception as exc:
        logger.error(f"Failed to save product '{raw.name}': {exc}")
        return None


@log_execution_time
def run_sourcing(target_per_wholesaler: int = None) -> int:
    """
    Scrape all wholesalers, persist new products, and return total count.
    Called at 06:00 and 14:00 daily.
    """
    per_site = target_per_wholesaler or (settings.DAILY_SOURCING_TARGET // len(CLIENTS))
    calc = MarginCalculator()
    db = SessionLocal()
    total = 0

    try:
        for ClientClass in CLIENTS:
            client = ClientClass()
            wholesaler = crud.get_or_create_wholesaler(
                db,
                name=client.wholesaler_name,
                base_url=WHOLESALER_URLS.get(client.wholesaler_name, ""),
            )

            try:
                products: List[RawProduct] = client.scrape_products(max_products=per_site)
            except Exception as exc:
                logger.error(f"Scraping failed for {client.wholesaler_name}: {exc}")
                products = []

            saved = 0
            for raw in products:
                p = _save_raw_product(db, raw, wholesaler, calc)
                if p:
                    saved += 1

            logger.info(f"[{client.wholesaler_name}] Saved {saved}/{len(products)} products.")
            total += saved

        # Update daily report
        report = crud.get_or_create_daily_report(db, datetime.utcnow().date())
        report.new_products_sourced = (report.new_products_sourced or 0) + total
        crud.save_daily_report(db, report)

        logger.info(f"Sourcing complete. Total new products: {total}")
        return total
    finally:
        db.close()
