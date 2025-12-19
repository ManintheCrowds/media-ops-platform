"""Health check API endpoints."""

from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import httpx
from app.models import Service, User
from app.auth.oauth2 import get_current_user, get_db

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
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
                "timestamp": datetime.utcnow().isoformat(),
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
                    service.last_health_check = datetime.utcnow()
                    db.commit()
                except Exception as e:
                    results[service.name] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
                    service.health_status = "unhealthy"
                    service.last_health_check = datetime.utcnow()
                    try:
                        db.commit()
                    except Exception:
                        db.rollback()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "services": results
        }
    except Exception as e:
        # Log the error and return a proper error response
        import traceback
        print(f"Error in check_all_services: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error checking services: {str(e)}"
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
            service.last_health_check = datetime.utcnow()
            db.commit()
            
            return {
                "service": service.name,
                "status": status,
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        service.health_status = "unhealthy"
        service.last_health_check = datetime.utcnow()
        db.commit()
        
        return {
            "service": service.name,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


