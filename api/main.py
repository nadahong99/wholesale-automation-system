from fastapi import FastAPI, BackgroundTasks
import logging

# Initialize the FastAPI app
app = FastAPI()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to initialize scheduler
async def initialize_scheduler():
    logger.info("Scheduler initialized")

# Startup event to initialize the scheduler
@app.on_event("startup")
asynchronous def startup_event():
    await initialize_scheduler()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI Application!"}

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
