import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from api.automation import check_low_stock, check_price_changes, generate_daily_order_summary
from api.routes import inventories, orders, price_histories, products, suppliers
from database.connection import engine
from database.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler():
    """Register automation jobs with the scheduler."""
    # Check low stock every hour
    scheduler.add_job(check_low_stock, "interval", hours=1, id="check_low_stock")
    # Check price changes every 30 minutes
    scheduler.add_job(check_price_changes, "interval", minutes=30, id="check_price_changes")
    # Generate daily order summary at midnight
    scheduler.add_job(
        generate_daily_order_summary,
        "cron",
        hour=0,
        minute=0,
        id="daily_order_summary",
    )
    scheduler.start()
    logger.info("Automation scheduler started.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    setup_scheduler()
    yield
    scheduler.shutdown()
    logger.info("Automation scheduler stopped.")


app = FastAPI(title="Wholesale Automation System", lifespan=lifespan)

app.include_router(suppliers.router)
app.include_router(products.router)
app.include_router(inventories.router)
app.include_router(orders.router)
app.include_router(price_histories.router)


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Wholesale Automation System."}


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error("An error occurred: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"},
    )
