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
        # Create directory if it doesn't exist
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
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
    """Initialize database on startup and verify credentials."""
    # Database tables will be created by Alembic migrations
    
    # Verify credentials are loaded (for debugging)
    import os
    from pathlib import Path
    from app.config import _find_env_file
    
    env_file = _find_env_file()
    env_exists = Path(env_file).exists()
    
    print("=" * 80)
    print("SERVER STARTUP - CREDENTIALS CHECK")
    print("=" * 80)
    print(f"Working Directory: {Path.cwd()}")
    print(f"Env File Path: {env_file}")
    print(f"Env File Exists: {env_exists}")
    print(f"Adzuna API ID: {settings.adzuna_api_id}")
    print(f"Adzuna API Key: {'Set' if settings.adzuna_api_key else 'NOT SET'}")
    print(f"JSearch API Key: {'Set' if settings.jsearch_api_key else 'NOT SET'}")
    
    # Test JobSourceManager
    from app.services.job_source_manager import JobSourceManager
    manager = JobSourceManager()
    has_adzuna = manager.has_api_client("adzuna")
    print(f"Has Adzuna Client: {has_adzuna}")
    
    if not has_adzuna:
        print("=" * 80)
        print("WARNING: Adzuna client not available!")
        print("Server will not be able to fetch jobs from Adzuna.")
        print("=" * 80)
    else:
        print("=" * 80)
        print("SUCCESS: All credentials loaded correctly")
        print("=" * 80)
    print()


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


@app.get("/debug/credentials")
async def debug_credentials():
    """Debug endpoint to check what credentials the server sees."""
    import os
    from pathlib import Path
    from app.services.job_source_manager import JobSourceManager
    from app.config import _find_env_file
    
    manager = JobSourceManager()
    env_file_path = _find_env_file()
    
    return {
        "working_directory": str(Path.cwd()),
        "env_file_path": env_file_path,
        "env_file_exists": Path(env_file_path).exists(),
        "adzuna_api_id": bool(settings.adzuna_api_id),
        "adzuna_api_id_value": settings.adzuna_api_id if settings.adzuna_api_id else None,
        "adzuna_api_key": bool(settings.adzuna_api_key),
        "adzuna_api_key_preview": settings.adzuna_api_key[:20] + "..." if settings.adzuna_api_key else None,
        "jsearch_api_key": bool(settings.jsearch_api_key),
        "has_adzuna_client": manager.has_api_client("adzuna"),
        "adzuna_client": str(manager.api_clients.get("adzuna")) if manager.api_clients.get("adzuna") else None,
        "env_vars": {
            "ADZUNA_API_ID": os.getenv("ADZUNA_API_ID", "NOT SET"),
            "ADZUNA_API_KEY": "SET" if os.getenv("ADZUNA_API_KEY") else "NOT SET",
        }
    }

