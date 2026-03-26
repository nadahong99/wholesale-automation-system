import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None


def _get_database_url() -> str:
    try:
        from config.settings import get_settings
        return get_settings().database_url
    except Exception:
        return "sqlite:///./wholesale.db"


def get_engine():
    global _engine
    if _engine is None:
        db_url = _get_database_url()
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        _engine = create_engine(
            db_url,
            connect_args=connect_args,
            echo=False,
            pool_pre_ping=True,
        )
        logger.info(f"Database engine created: {db_url}")
    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


# Convenience alias used across the app
engine = None  # Will be lazily set via get_engine()
SessionLocal = None  # Will be lazily set via get_session_factory()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a database session."""
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables in the database."""
    eng = get_engine()
    Base.metadata.create_all(bind=eng)
    logger.info("Database tables created / verified")
