import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from database.connection import engine
from database.models import Base
from api.routes import suppliers, products, orders, price_histories, inventories

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

# Initialize the FastAPI app
app = FastAPI(title="Wholesale Automation System")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register routers
app.include_router(suppliers.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(price_histories.router)
app.include_router(inventories.router)


# Function to initialize scheduler
async def initialize_scheduler():
    logger.info("Scheduler initialized")


# Startup event to initialize the scheduler
@app.on_event("startup")
async def startup_event():
    await initialize_scheduler()


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Wholesale Automation System!"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}


# Error handling example
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"An error occurred: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"}
    )
