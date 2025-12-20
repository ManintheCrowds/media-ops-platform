"""Main FastAPI application for Educational System Service."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api import content

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include routers
app.include_router(content.router, prefix="/api/v1/education", tags=["content"])
from app.api import taxonomy, projects, integrations
from app.api.pi import devices, sync, content as pi_content, iot, streaming, security
app.include_router(taxonomy.router, prefix="/api/v1/education", tags=["taxonomy"])
app.include_router(projects.router, prefix="/api/v1/education", tags=["projects"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])
app.include_router(devices.router, prefix="/api/v1/pi", tags=["pi-devices"])
app.include_router(sync.router, prefix="/api/v1/pi", tags=["pi-sync"])
app.include_router(pi_content.router, prefix="/api/v1/pi", tags=["pi-content"])
app.include_router(iot.router, prefix="/api/v1/pi", tags=["pi-iot"])
app.include_router(streaming.router, prefix="/api/v1/pi", tags=["pi-streaming"])
app.include_router(security.router, prefix="/api/v1/pi", tags=["pi-security"])


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



