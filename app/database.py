"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config import settings
from app.models import Base

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
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
