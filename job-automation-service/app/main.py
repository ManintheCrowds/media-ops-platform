"""Main FastAPI application for Job Application Automation Service."""

import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base
from app.api import jobs, applications, matching, scheduler

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
log_entry("server-startup", "run1", "H-STARTUP", "app/main.py", "FastAPI app module loading", {
    "python": __import__('sys').executable
})
# #endregion agent log

# Create FastAPI app
# #region agent log
log_entry("server-startup", "run1", "H-STARTUP", "app/main.py", "Creating FastAPI app", {
    "app_name": settings.app_name,
    "version": settings.app_version
})
# #endregion agent log

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
)

# #region agent log
log_entry("server-startup", "run1", "H-STARTUP", "app/main.py", "FastAPI app created", {
    "success": True
})
# #endregion agent log

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include routers
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(matching.router)
app.include_router(scheduler.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    # Database tables will be created by Alembic migrations
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    pass


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

