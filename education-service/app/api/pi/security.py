"""Raspberry Pi security API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, UserInfo
from app.services.pi_service import PiDeviceService
from app.services.security_service import SecurityService

router = APIRouter()


@router.post("/devices/{device_id}/certificates/register")
async def register_certificate(
    device_id: str,
    certificate_data: str,
    fingerprint: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Register device certificate."""
    device = PiDeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    cert = SecurityService.register_certificate(
        db,
        device_id=device.id,
        certificate_data=certificate_data,
        fingerprint=fingerprint
    )
    
    return {
        "status": "registered",
        "certificate_id": cert.id,
        "fingerprint": cert.fingerprint,
    }


@router.post("/devices/{device_id}/certificates/renew")
async def renew_certificate(
    device_id: str,
    certificate_data: str,
    fingerprint: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Renew device certificate."""
    device = PiDeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    cert = SecurityService.renew_certificate(
        db,
        device_id=device.id,
        certificate_data=certificate_data,
        fingerprint=fingerprint
    )
    
    return {
        "status": "renewed",
        "certificate_id": cert.id,
        "fingerprint": cert.fingerprint,
    }


@router.get("/devices/{device_id}/security/status")
async def get_security_status(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Get device security status."""
    device = PiDeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return {
        "device_id": device.device_id,
        "security_status": device.security_status,
        "certificate_fingerprint": device.certificate_fingerprint,
        "last_seen": device.last_seen,
    }


@router.post("/devices/{device_id}/wipe")
async def initiate_wipe(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Initiate remote wipe for device."""
    device = PiDeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Only admins can initiate wipe
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can initiate remote wipe"
        )
    
    SecurityService.initiate_wipe(db, device_id=device.id)
    
    return {
        "status": "wipe_initiated",
        "device_id": device_id,
    }



