"""Database configuration and session management."""

import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

LOG_PATH = Path(r"d:\CodeRepositories\.cursor\debug.log")

def log_entry(session_id, run_id, hypothesis_id, location, message, data):
    """Write debug log entry."""
    entry = {
        "sessionId": session_id,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(__import__('time').time() * 1000)
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

# #region agent log
log_entry("db-init", "run1", "H-DB-ENGINE", "app/database.py", "Creating database engine", {
    "database_url": settings.database_url.split("@")[-1] if "@" in settings.database_url else "hidden"
})
# #endregion agent log

# Create database engine with lazy connection
# pool_pre_ping=True will test connections before using them, but won't connect on engine creation
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"connect_timeout": 5},  # 5 second timeout for connection attempts
)

# #region agent log
log_entry("db-init", "run1", "H-DB-ENGINE", "app/database.py", "Database engine created", {
    "success": True,
    "lazy_connection": True
})
# #endregion agent log

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

