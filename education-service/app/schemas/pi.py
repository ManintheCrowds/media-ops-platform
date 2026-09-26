"""Pydantic schemas for Raspberry Pi device management."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.pi_device import DeviceType, SyncStatus, PackageType, PackageStatus


class PiDeviceBase(BaseModel):
    """Base Pi device schema."""
    device_name: str = Field(..., min_length=1, max_length=255)
    device_type: DeviceType
    capabilities: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None


class PiDeviceCreate(PiDeviceBase):
    """Schema for creating a Pi device."""
    device_id: str = Field(..., min_length=1, max_length=255)
    organization_id: int


class PiDeviceUpdate(BaseModel):
    """Schema for updating a Pi device."""
    device_name: Optional[str] = Field(None, min_length=1, max_length=255)
    capabilities: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None


class PiDeviceResponse(PiDeviceBase):
    """Schema for Pi device response."""
    id: int
    device_id: str
    organization_id: int
    last_sync: Optional[datetime] = None
    sync_status: SyncStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PiSyncPackageResponse(BaseModel):
    """Schema for sync package response."""
    id: int
    device_id: int
    package_type: PackageType
    content_ids: List[int]
    package_url: Optional[str] = None
    package_path: Optional[str] = None
    package_size: Optional[int] = None
    checksum: Optional[str] = None
    status: PackageStatus = PackageStatus.PENDING
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SyncCheckResponse(BaseModel):
    """Schema for sync check response."""
    has_updates: bool
    last_sync: Optional[datetime] = None
    sync_status: SyncStatus
    available_packages: List[PiSyncPackageResponse] = []


class SyncCompleteRequest(BaseModel):
    """Body for marking sync complete."""
    package_id: int


class DeviceTokenResponse(BaseModel):
    """Device-scoped access token."""
    access_token: str
    token_type: str = "bearer"
    device_id: str
    expires_in_minutes: int
