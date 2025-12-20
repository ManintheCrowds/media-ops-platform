"""Raspberry Pi device service."""

from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from app.models.pi_device import PiDevice, PiSyncPackage, DeviceType, SyncStatus, PackageType
from app.models.organization import Organization
from app.schemas.pi import PiDeviceCreate, PiDeviceUpdate
from app.auth.platform_auth import UserInfo


class PiDeviceService:
    """Service for Pi device management."""
    
    @staticmethod
    def register_device(
        db: Session,
        device_data: PiDeviceCreate,
        user: UserInfo
    ) -> PiDevice:
        """Register a new Pi device."""
        # Verify organization exists
        org = db.query(Organization).filter(Organization.id == device_data.organization_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Check if device_id already exists
        existing = db.query(PiDevice).filter(PiDevice.device_id == device_data.device_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device with this ID already exists"
            )
        
        # Create device
        device = PiDevice(
            device_id=device_data.device_id,
            device_name=device_data.device_name,
            device_type=device_data.device_type,
            organization_id=device_data.organization_id,
            capabilities=device_data.capabilities or {},
            settings=device_data.settings or {},
            sync_status=SyncStatus.SYNCED
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
        device_data: PiDeviceUpdate
    ) -> PiDevice:
        """Update device configuration."""
        device = PiDeviceService.get_device(db, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
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
                detail="Device not found"
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
    def check_for_updates(
        db: Session,
        device_id: str
    ) -> Dict:
        """Check if device has available updates."""
        device = PiDeviceService.get_device(db, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Get available packages that haven't expired
        now = datetime.now(timezone.utc)
        packages = db.query(PiSyncPackage).filter(
            PiSyncPackage.device_id == device.id,
            PiSyncPackage.expires_at > now
        ).order_by(PiSyncPackage.created_at.desc()).all()
        
        has_updates = len(packages) > 0
        
        return {
            "has_updates": has_updates,
            "last_sync": device.last_sync,
            "sync_status": device.sync_status,
            "available_packages": packages,
        }
    
    @staticmethod
    def request_sync_package(
        db: Session,
        device_id: str,
        package_type: PackageType,
        content_ids: Optional[List[int]] = None
    ) -> PiSyncPackage:
        """Request/create a sync package for device."""
        device = PiDeviceService.get_device(db, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Update device sync status
        device.sync_status = SyncStatus.SYNCING
        db.commit()
        
        # Create sync package
        package = PiSyncPackage(
            device_id=device.id,
            package_type=package_type,
            content_ids=content_ids or [],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)  # 24 hour expiry
        )
        
        db.add(package)
        db.commit()
        db.refresh(package)
        
        # Note: Package generation and URL assignment would happen in background task
        # For now, we just create the package record
        
        return package
    
    @staticmethod
    def mark_sync_complete(
        db: Session,
        device_id: str,
        package_id: int
    ) -> bool:
        """Mark sync as complete."""
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
        
        device.sync_status = SyncStatus.SYNCED
        device.last_sync = datetime.now(timezone.utc)
        
        db.commit()
        
        return True



