"""Raspberry Pi device service."""

from __future__ import annotations

import hashlib
import json
import logging
import tarfile
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.platform_auth import UserInfo
from app.config import settings
from app.models.organization import Organization
from app.models.pi_device import (
    PackageStatus,
    PackageType,
    PiDevice,
    PiSyncPackage,
    SyncStatus,
)
from app.schemas.pi import PiDeviceCreate, PiDeviceUpdate

logger = logging.getLogger(__name__)


class PiDeviceService:
    """Service for Pi device management."""

    @staticmethod
    def register_device(
        db: Session,
        device_data: PiDeviceCreate,
        user: UserInfo,
    ) -> PiDevice:
        """Register a new Pi device."""
        org = db.query(Organization).filter(Organization.id == device_data.organization_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        existing = db.query(PiDevice).filter(PiDevice.device_id == device_data.device_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device with this ID already exists",
            )

        device = PiDevice(
            device_id=device_data.device_id,
            device_name=device_data.device_name,
            device_type=device_data.device_type,
            organization_id=device_data.organization_id,
            capabilities=device_data.capabilities or {},
            settings=device_data.settings or {},
            sync_status=SyncStatus.SYNCED,
        )

        db.add(device)
        db.commit()
        db.refresh(device)

        return device

    @staticmethod
    def get_device(db: Session, device_id: str) -> Optional[PiDevice]:
        """Get device by device_id."""
        return db.query(PiDevice).filter(PiDevice.device_id == device_id).first()

    @staticmethod
    def update_device(
        db: Session,
        device_id: str,
        device_data: PiDeviceUpdate,
    ) -> PiDevice:
        """Update device configuration."""
        device = PiDeviceService.get_device(db, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        if device_data.device_name is not None:
            device.device_name = device_data.device_name

        if device_data.capabilities is not None:
            device.capabilities = device_data.capabilities

        if device_data.settings is not None:
            device.settings = device_data.settings

        db.commit()
        db.refresh(device)

        return device

    @staticmethod
    def get_device_status(db: Session, device_id: str) -> Dict:
        """Get device sync status."""
        device = PiDeviceService.get_device(db, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        return {
            "device_id": device.device_id,
            "device_name": device.device_name,
            "sync_status": device.sync_status,
            "last_sync": device.last_sync,
            "capabilities": device.capabilities,
        }


class PiSyncService:
    """Service for Pi device content synchronization."""

    @staticmethod
    def _storage_root() -> Path:
        root = Path(settings.sync_package_storage_path)
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def build_package_archive(package: PiSyncPackage, dest: Path) -> None:
        """Build a minimal tar.gz for the package content IDs."""
        with tarfile.open(dest, "w:gz") as tar:
            content_ids = package.content_ids or []
            for content_id in content_ids:
                prefix = f"content_{content_id}"
                metadata = {
                    "id": content_id,
                    "package_id": package.id,
                    "package_type": package.package_type.value
                    if hasattr(package.package_type, "value")
                    else str(package.package_type),
                }
                with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
                    json.dump(metadata, tmp)
                    tmp_path = Path(tmp.name)
                try:
                    tar.add(tmp_path, arcname=f"{prefix}/metadata.json")
                finally:
                    tmp_path.unlink(missing_ok=True)

    @staticmethod
    def materialize_package(db: Session, package: PiSyncPackage) -> PiSyncPackage:
        """Write archive bytes, checksum, and mark ready or failed."""
        try:
            dest = PiSyncService._storage_root() / f"package_{package.id}.tar.gz"
            PiSyncService.build_package_archive(package, dest)
            package.package_path = str(dest)
            package.package_size = dest.stat().st_size
            package.checksum = PiSyncService._sha256_file(dest)
            package.status = PackageStatus.READY
        except Exception as exc:  # noqa: BLE001
            logger.exception("Package build failed for package_id=%s", package.id)
            package.status = PackageStatus.FAILED
            package.checksum = None
            package.package_path = None
            package.package_size = None
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Package generation failed: {exc}",
            ) from exc
        finally:
            db.commit()
            db.refresh(package)
        return package

    @staticmethod
    def check_for_updates(db: Session, device_id: str) -> Dict:
        """Check if device has downloadable ready packages."""
        device = PiDeviceService.get_device(db, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        now = datetime.now(timezone.utc)
        packages = (
            db.query(PiSyncPackage)
            .filter(
                PiSyncPackage.device_id == device.id,
                PiSyncPackage.status == PackageStatus.READY,
                PiSyncPackage.checksum.isnot(None),
                PiSyncPackage.expires_at > now,
            )
            .order_by(PiSyncPackage.created_at.desc())
            .all()
        )

        ready = [
            p
            for p in packages
            if p.checksum and p.package_path and Path(p.package_path).is_file()
        ]

        return {
            "has_updates": len(ready) > 0,
            "last_sync": device.last_sync,
            "sync_status": device.sync_status,
            "available_packages": ready,
        }

    @staticmethod
    def request_sync_package(
        db: Session,
        device_id: str,
        package_type: PackageType,
        content_ids: Optional[List[int]] = None,
    ) -> PiSyncPackage:
        """Request/create a sync package and materialize it to ready."""
        device = PiDeviceService.get_device(db, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        device.sync_status = SyncStatus.SYNCING
        package = PiSyncPackage(
            device_id=device.id,
            package_type=package_type,
            content_ids=content_ids or [],
            status=PackageStatus.PENDING,
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=settings.sync_package_expiry_hours),
        )
        db.add(package)
        db.commit()
        db.refresh(package)

        return PiSyncService.materialize_package(db, package)

    @staticmethod
    def get_ready_package(
        db: Session, device_id: str, package_id: int
    ) -> PiSyncPackage:
        """Load a ready package for download or raise."""
        device = PiDeviceService.get_device(db, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        package = (
            db.query(PiSyncPackage)
            .filter(
                PiSyncPackage.id == package_id,
                PiSyncPackage.device_id == device.id,
            )
            .first()
        )
        if not package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sync package not found",
            )
        return package

    @staticmethod
    def mark_sync_complete(db: Session, device_id: str, package_id: int) -> bool:
        """Mark sync as complete."""
        device = PiDeviceService.get_device(db, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        package = (
            db.query(PiSyncPackage)
            .filter(
                PiSyncPackage.id == package_id,
                PiSyncPackage.device_id == device.id,
            )
            .first()
        )

        if not package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sync package not found",
            )

        device.sync_status = SyncStatus.SYNCED
        device.last_sync = datetime.now(timezone.utc)

        db.commit()

        return True
