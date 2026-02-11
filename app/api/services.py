"""Service management API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone
from app.models import Service, User
from app.auth.oauth2 import get_current_user
from app.database import get_db
from app.validation import validate_service_url
from app.config import settings
from app.utils.error_responses import ErrorCodes

router = APIRouter()


class ServiceCreate(BaseModel):
    """Service creation model."""
    name: str
    service_type: str
    base_url: str
    api_url: Optional[str] = None
    health_check_url: Optional[str] = None
    requires_auth: bool = True
    auth_token: Optional[str] = None
    metadata: Optional[str] = None


class ServiceResponse(BaseModel):
    """Service response model."""
    id: int
    name: str
    service_type: str
    base_url: str
    api_url: Optional[str]
    health_check_url: Optional[str]
    is_active: bool
    requires_auth: bool
    health_status: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[ServiceResponse])
async def list_services(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[ServiceResponse]:
    """List all registered services."""
    services = db.query(Service).filter(Service.is_active == True).all()
    return services


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ServiceResponse:
    """Get a specific service by ID."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Service not found",
                "error_code": ErrorCodes.NOT_FOUND,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        )
    return service


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ServiceResponse:
    """Register a new service."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Only admins can register services",
                "error_code": ErrorCodes.AUTHORIZATION_ERROR,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        )
    
    # Check if service name already exists
    if db.query(Service).filter(Service.name == service_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Service name already exists",
                "error_code": ErrorCodes.CONFLICT,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        )
    
    # Validate service URLs to prevent SSRF attacks
    urls_to_validate = [
        ("base_url", service_data.base_url),
        ("api_url", service_data.api_url),
        ("health_check_url", service_data.health_check_url)
    ]
    
    for url_field, url_value in urls_to_validate:
        if url_value:
            is_valid, error_message = validate_service_url(
                url_value,
                allowed_internal_patterns=settings.ssrf_allowed_internal_patterns
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": f"Invalid {url_field}: {error_message}",
                        "error_code": ErrorCodes.VALIDATION_ERROR,
                        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    }
                )
    
    service = Service(**service_data.dict())
    db.add(service)
    db.commit()
    db.refresh(service)
    
    return service


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,
    service_data: ServiceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ServiceResponse:
    """Update a service."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Only admins can update services",
                "error_code": ErrorCodes.AUTHORIZATION_ERROR,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        )
    
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Service not found",
                "error_code": ErrorCodes.NOT_FOUND,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        )
    
    # Validate service URLs to prevent SSRF attacks
    urls_to_validate = [
        ("base_url", service_data.base_url),
        ("api_url", service_data.api_url),
        ("health_check_url", service_data.health_check_url)
    ]
    
    for url_field, url_value in urls_to_validate:
        if url_value:
            is_valid, error_message = validate_service_url(
                url_value,
                allowed_internal_patterns=settings.ssrf_allowed_internal_patterns
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": f"Invalid {url_field}: {error_message}",
                        "error_code": ErrorCodes.VALIDATION_ERROR,
                        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    }
                )
    
    for key, value in service_data.dict().items():
        setattr(service, key, value)
    
    db.commit()
    db.refresh(service)
    
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """Delete a service."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Only admins can delete services",
                "error_code": ErrorCodes.AUTHORIZATION_ERROR,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        )
    
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Service not found",
                "error_code": ErrorCodes.NOT_FOUND,
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        )
    
    db.delete(service)
    db.commit()
    
    return None


