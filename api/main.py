# api/main.py
"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database.session import init_db
from api.routes import sourcing, orders, monitoring
from api.models import HealthResponse
from config.settings import settings
from utils.logger import get_logger

logger = get_logger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up – initialising database…")
    init_db()
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Wholesale Automation System",
    description="AI-powered Korean wholesale automation platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sourcing.router)
app.include_router(orders.router)
app.include_router(monitoring.router)


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
