import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import sourcing, orders, monitoring

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup
    try:
        from config.logging_config import setup_logging
        setup_logging()
    except Exception:
        pass
    try:
        from database.session import init_db
        init_db()
        logger.info("Database initialized on startup")
    except Exception as exc:
        logger.error(f"DB init failed: {exc}")
    yield
    # Shutdown
    logger.info("Application shutdown")


app = FastAPI(
    title="Wholesale Automation API",
    version="1.0.0",
    description="Production-ready wholesale automation system for Korean e-commerce platforms",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} duration={elapsed:.1f}ms"
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "path": str(request.url.path)},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


app.include_router(sourcing.router)
app.include_router(orders.router)
app.include_router(monitoring.router)


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "wholesale-automation-api",
    }


@app.get("/", tags=["root"])
def root():
    """Root endpoint with API info."""
    return {
        "name": "Wholesale Automation API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
