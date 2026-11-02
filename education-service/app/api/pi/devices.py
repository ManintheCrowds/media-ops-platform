"""Raspberry Pi device management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.device_auth import create_device_token
from app.auth.platform_auth import UserInfo
from app.database import get_db
from app.dependencies import get_current_admin_user, get_current_user
from app.schemas.pi import (
    DeviceTokenResponse,
    PiDeviceCreate,
    PiDeviceResponse,
    PiDeviceUpdate,
)
from app.services.pi_service import PiDeviceService

router = APIRouter()

DEVICE_TOKEN_TTL_MINUTES = 60 * 24 * 30


@router.post(
    "/devices/register",
    response_model=PiDeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
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
            detail="Device not found",
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
    return PiDeviceService.get_device_status(db, device_id)


@router.post(
    "/devices/{device_id}/tokens",
    response_model=DeviceTokenResponse,
)
async def mint_device_token(
    device_id: str,
    db: Session = Depends(get_db),
    _admin: UserInfo = Depends(get_current_admin_user),
):
    """Mint a device-scoped JWT for Pi sync (admin only)."""
    device = PiDeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    token = create_device_token(device.device_id, expires_minutes=DEVICE_TOKEN_TTL_MINUTES)
    return DeviceTokenResponse(
        access_token=token,
        device_id=device.device_id,
        expires_in_minutes=DEVICE_TOKEN_TTL_MINUTES,
    )
