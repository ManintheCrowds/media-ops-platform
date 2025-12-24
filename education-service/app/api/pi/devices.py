"""Raspberry Pi device management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, UserInfo
from app.schemas.pi import (
    PiDeviceCreate,
    PiDeviceUpdate,
    PiDeviceResponse,
    SyncCheckResponse,
    PiSyncPackageResponse,
)
from app.services.pi_service import PiDeviceService, PiSyncService
from app.models.pi_device import PackageType

router = APIRouter()


@router.post("/devices/register", response_model=PiDeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    device_data: PiDeviceCreate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Register a new Raspberry Pi device."""
    device = PiDeviceService.register_device(db, device_data, current_user)
    return PiDeviceResponse.model_validate(device)


@router.get("/devices/{device_id}", response_model=PiDeviceResponse)
async def get_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Get device information."""
    device = PiDeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    return PiDeviceResponse.model_validate(device)


@router.put("/devices/{device_id}", response_model=PiDeviceResponse)
async def update_device(
    device_id: str,
    device_data: PiDeviceUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Update device configuration."""
    device = PiDeviceService.update_device(db, device_id, device_data)
    return PiDeviceResponse.model_validate(device)


@router.get("/devices/{device_id}/status")
async def get_device_status(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Get device sync status."""
    status_data = PiDeviceService.get_device_status(db, device_id)
    return status_data







