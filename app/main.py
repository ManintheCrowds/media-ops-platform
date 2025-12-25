"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.api import services, health, gateway, scheduler
from app.auth import oauth2, jwt_handler
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug and settings.enable_debug_endpoints  # More restrictive
)

# Static files and templates
static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")
templates_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir) if os.path.exists(templates_dir) else None

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Global exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that sanitizes error messages in production."""
    # Log full error details server-side
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Return sanitized error to client
    if settings.debug:
        # In debug mode, return detailed error
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
                "path": str(request.url)
            }
        )
    else:
        # In production, return generic error
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred"}
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with appropriate detail level."""
    if settings.debug:
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "body": exc.body}
        )
    else:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid request data"}
        )


# Include routers
app.include_router(oauth2.router, prefix="/api/auth", tags=["authentication"])
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(gateway.router, prefix="/api/gateway", tags=["gateway"])
app.include_router(scheduler.router, prefix="/api/v1/scheduler", tags=["scheduler"])


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with dashboard redirect."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Self-Hosted Platform</title>
        <meta http-equiv="refresh" content="0; url=/dashboard">
    </head>
    <body>
        <p>Redirecting to <a href="/dashboard">dashboard</a>...</p>
    </body>
    </html>
    """


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page."""
    if templates:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    return HTMLResponse(content="Dashboard not available", status_code=503)


@app.get("/login.html", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    if templates:
        return templates.TemplateResponse("login.html", {"request": request})
    return HTMLResponse(content="Login page not available", status_code=503)


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "endpoints": {
            "auth": "/api/auth",
            "services": "/api/services",
            "health": "/api/health",
            "gateway": "/api/gateway",
            "scheduler": "/api/v1/scheduler"
        }
    }

