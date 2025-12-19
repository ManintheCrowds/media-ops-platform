"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.config import settings
from app.api import services, health, gateway
from app.auth import oauth2, jwt_handler
import os

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
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

# Include routers
app.include_router(oauth2.router, prefix="/api/auth", tags=["authentication"])
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(gateway.router, prefix="/api/gateway", tags=["gateway"])


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
            "gateway": "/api/gateway"
        }
    }

