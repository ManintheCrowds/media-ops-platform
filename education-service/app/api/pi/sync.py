"""Raspberry Pi content synchronization API endpoints."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, UserInfo
from app.schemas.pi import SyncCheckResponse, PiSyncPackageResponse
from app.services.pi_service import PiSyncService
from app.models.pi_device import PackageType

router = APIRouter()


@router.get("/devices/{device_id}/sync/check", response_model=SyncCheckResponse)
async def check_for_updates(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Check for available content updates."""
    result = PiSyncService.check_for_updates(db, device_id)
    return SyncCheckResponse(
        has_updates=result["has_updates"],
        last_sync=result["last_sync"],
        sync_status=result["sync_status"],
        available_packages=[PiSyncPackageResponse.model_validate(p) for p in result["available_packages"]],
    )


@router.post("/devices/{device_id}/sync/request", response_model=PiSyncPackageResponse)
async def request_sync_package(
    device_id: str,
    package_type: PackageType = Query(..., description="Type of sync package"),
    content_ids: Optional[List[int]] = Query(None, description="Specific content IDs to include"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Request a sync package for device."""
    package = PiSyncService.request_sync_package(db, device_id, package_type, content_ids)
    return PiSyncPackageResponse.model_validate(package)


@router.get("/devices/{device_id}/sync/packages/{package_id}/download")
async def download_sync_package(
    device_id: str,
    package_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Download sync package."""
    # This would return the actual package file
    # For now, return package info
    from app.models.pi_device import PiSyncPackage
    from app.services.pi_service import PiDeviceService
    
    device = PiDeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    package = db.query(PiSyncPackage).filter(
        PiSyncPackage.id == package_id,
        PiSyncPackage.device_id == device.id
    ).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync package not found"
        )
    
    if package.package_url:
        return {"download_url": package.package_url, "package_id": package.id}
    else:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Package is being generated, please check back later"
        )


@router.post("/devices/{device_id}/sync/complete", status_code=status.HTTP_200_OK)
async def mark_sync_complete(
    device_id: str,
    package_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Mark sync as complete."""
    PiSyncService.mark_sync_complete(db, device_id, package_id)
    return {"status": "completed"}




