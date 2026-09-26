"""Raspberry Pi content synchronization API endpoints."""

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.device_auth import DevicePrincipal
from app.database import get_db
from app.dependencies import get_current_device
from app.models.pi_device import PackageStatus, PackageType
from app.schemas.pi import PiSyncPackageResponse, SyncCheckResponse, SyncCompleteRequest
from app.services.pi_service import PiSyncService

router = APIRouter()


@router.get("/devices/{device_id}/sync/check", response_model=SyncCheckResponse)
async def check_for_updates(
    device_id: str,
    db: Session = Depends(get_db),
    _device: DevicePrincipal = Depends(get_current_device),
):
    """Check for available content updates."""
    result = PiSyncService.check_for_updates(db, device_id)
    return SyncCheckResponse(
        has_updates=result["has_updates"],
        last_sync=result["last_sync"],
        sync_status=result["sync_status"],
        available_packages=[
            PiSyncPackageResponse.model_validate(p) for p in result["available_packages"]
        ],
    )


@router.post("/devices/{device_id}/sync/request", response_model=PiSyncPackageResponse)
async def request_sync_package(
    device_id: str,
    package_type: PackageType = Query(..., description="Type of sync package"),
    content_ids: Optional[List[int]] = Query(
        None, description="Specific content IDs to include"
    ),
    db: Session = Depends(get_db),
    _device: DevicePrincipal = Depends(get_current_device),
):
    """Request a sync package for device."""
    package = PiSyncService.request_sync_package(
        db, device_id, package_type, content_ids
    )
    return PiSyncPackageResponse.model_validate(package)


@router.get("/devices/{device_id}/sync/packages/{package_id}/download")
async def download_sync_package(
    device_id: str,
    package_id: int,
    db: Session = Depends(get_db),
    _device: DevicePrincipal = Depends(get_current_device),
):
    """Stream sync package bytes when ready."""
    package = PiSyncService.get_ready_package(db, device_id, package_id)

    if package.status == PackageStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Package is being generated, please check back later",
        )

    if package.status != PackageStatus.READY or not package.package_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Package not ready for download (status={package.status})",
        )

    path = Path(package.package_path)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package file missing on server",
        )

    def iterfile():
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(65536)
                if not chunk:
                    break
                yield chunk

    headers = {
        "Content-Disposition": f'attachment; filename="package_{package_id}.tar.gz"',
        "X-Package-Checksum": package.checksum or "",
    }
    return StreamingResponse(
        iterfile(),
        media_type="application/gzip",
        headers=headers,
    )


@router.post("/devices/{device_id}/sync/complete", status_code=status.HTTP_200_OK)
async def mark_sync_complete(
    device_id: str,
    body: SyncCompleteRequest,
    db: Session = Depends(get_db),
    _device: DevicePrincipal = Depends(get_current_device),
):
    """Mark sync as complete."""
    PiSyncService.mark_sync_complete(db, device_id, body.package_id)
    return {"status": "completed", "package_id": body.package_id}
