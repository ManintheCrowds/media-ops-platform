"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from .config import config
from .base import Base

# Create engine
engine = create_engine(
    config.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    # Import all model classes to ensure they're registered with Base.metadata
    from .models.security_events import SecurityEvent
    from .models.incidents import SecurityIncident
    from .models.threats import (
        ThreatIntelligence,
        FirewallRule,
        VulnerabilityScan,
        PatchStatus,
        AuditLog
    )
    
    Base.metadata.create_all(bind=engine)




