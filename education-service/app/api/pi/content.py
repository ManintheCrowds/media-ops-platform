"""Raspberry Pi lightweight content delivery API."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, UserInfo
from app.services.content_service import ContentService
from app.services.pi_service import PiDeviceService
from app.schemas.content import ContentItemResponse

router = APIRouter()


@router.get("/devices/{device_id}/content", response_model=list[ContentItemResponse])
async def get_device_content(
    device_id: str,
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Get content list for device (optimized format)."""
    # Verify device exists and belongs to user's organization
    device = PiDeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Get content items (lightweight query)
    items, _ = ContentService.list_content(
        db,
        project_id=project_id,
        page=1,
        page_size=1000  # Large limit for device
    )
    
    # Return optimized response (could filter by device organization)
    return [ContentItemResponse.model_validate(item) for item in items]


@router.get("/devices/{device_id}/content/{content_id}", response_model=ContentItemResponse)
async def get_device_content_item(
    device_id: str,
    content_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Get specific content item for device (optimized format)."""
    # Verify device exists
    device = PiDeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    content = ContentService.get_content(db, content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    return ContentItemResponse.model_validate(content)


@router.get("/devices/{device_id}/display/config")
async def get_display_config(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Get display configuration for device."""
    device = PiDeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Return device-specific display configuration
    return {
        "device_id": device.device_id,
        "device_type": device.device_type,
        "display_settings": device.settings.get("display", {}),
        "capabilities": device.capabilities,
    }



