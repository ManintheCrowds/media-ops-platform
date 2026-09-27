"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config import settings
from app.models import Base

_engine_kwargs: dict = {"pool_pre_ping": True}
_connect_args: dict = {}
if settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
else:
    _engine_kwargs.update(pool_size=10, max_overflow=20)

# Create engine with connection pooling (Postgres) or sqlite-safe args
engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    **_engine_kwargs,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    # Import all models to ensure they're registered
    from app.models import User, Service
    from app.models.camera import ArloBaseStation, ArloCamera, ArloRecording, ArloEvent
    from app.models.encoder import VideoEncoder
    
    Base.metadata.create_all(bind=engine)
