"""Health check API endpoints."""

from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import httpx
import logging
from app.models import Service, User
from app.auth.oauth2 import get_current_user
from app.database import get_db
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/services")
async def check_all_services(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Check health of all registered services."""
    try:
        services = db.query(Service).filter(Service.is_active == True).all()
        results = {}
        
        # If no services are registered, return empty results
        if not services:
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "services": {}
            }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for service in services:
                health_url = service.health_check_url or f"{service.base_url}/health"
                try:
                    response = await client.get(health_url)
                    status = "healthy" if response.status_code == 200 else "unhealthy"
                    results[service.name] = {
                        "status": status,
                        "status_code": response.status_code,
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    }
                    
                    # Update service health status
                    service.health_status = status
                    service.last_health_check = datetime.now(timezone.utc)
                    db.commit()
                except Exception as e:
                    logger.error(f"Error checking service {service.name}: {e}", exc_info=True)
                    error_detail = str(e) if settings.debug else "Service check failed"
                    results[service.name] = {
                        "status": "unhealthy",
                        "error": error_detail
                    }
                    service.health_status = "unhealthy"
                    service.last_health_check = datetime.now(timezone.utc)
                    try:
                        db.commit()
                    except Exception:
                        db.rollback()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": results
        }
    except Exception as e:
        # Log the error and return a proper error response
        logger.error(f"Error in check_all_services: {e}", exc_info=True)
        error_detail = f"Error checking services: {str(e)}" if settings.debug else "Error checking services"
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )


@router.get("/services/{service_id}")
async def check_service(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Check health of a specific service."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        return {
            "status": "not_found",
            "error": "Service not found"
        }
    
    health_url = service.health_check_url or f"{service.base_url}/health"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(health_url)
            status = "healthy" if response.status_code == 200 else "unhealthy"
            
            # Update service health status
            service.health_status = status
            service.last_health_check = datetime.now(timezone.utc)
            db.commit()
            
            return {
                "service": service.name,
                "status": status,
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        logger.error(f"Error checking service {service.id}: {e}", exc_info=True)
        service.health_status = "unhealthy"
        service.last_health_check = datetime.now(timezone.utc)
        db.commit()
        
        error_detail = str(e) if settings.debug else "Service check failed"
        return {
            "service": service.name,
            "status": "unhealthy",
            "error": error_detail,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


