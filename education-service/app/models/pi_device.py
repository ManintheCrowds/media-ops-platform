"""Raspberry Pi device models."""

from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Enum as SQLEnum, JSON, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class DeviceType(str, enum.Enum):
    """Device type enum."""
    KIOSK = "kiosk"
    INTERACTIVE = "interactive"
    SYNC = "sync"
    IOT = "iot"


class SyncStatus(str, enum.Enum):
    """Sync status enum."""
    SYNCED = "synced"
    SYNCING = "syncing"
    ERROR = "error"


class SecurityStatus(str, enum.Enum):
    """Security status enum."""
    ACTIVE = "active"
    REVOKED = "revoked"
    WIPED = "wiped"


class PackageType(str, enum.Enum):
    """Package type enum."""
    FULL = "full"
    INCREMENTAL = "incremental"
    CONTENT_ONLY = "content_only"


class PiDevice(Base):
    """Raspberry Pi device model."""
    
    __tablename__ = "pi_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(255), unique=True, nullable=False, index=True)
    device_name = Column(String(255), nullable=False)
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    sync_status = Column(SQLEnum(SyncStatus), default=SyncStatus.SYNCED, nullable=False)
    capabilities = Column(JSON)  # Device capabilities
    settings = Column(JSON)  # Device configuration
    certificate_fingerprint = Column(String(64), nullable=True, index=True)
    security_status = Column(SQLEnum(SecurityStatus), default=SecurityStatus.ACTIVE, nullable=False)
    encryption_key = Column(String(500), nullable=True)  # Encrypted device key
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="pi_devices")
    sync_packages = relationship("PiSyncPackage", back_populates="device", cascade="all, delete-orphan")


class PiSyncPackage(Base):
    """Raspberry Pi sync package model."""
    
    __tablename__ = "pi_sync_packages"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("pi_devices.id"), nullable=False, index=True)
    package_type = Column(SQLEnum(PackageType), nullable=False)
    content_ids = Column(JSON)  # Array of content item IDs
    package_url = Column(String(500))  # Download URL
    package_size = Column(BigInteger)  # Size in bytes
    checksum = Column(String(64))  # SHA256 checksum
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    device = relationship("PiDevice", back_populates="sync_packages")


class DeviceCertificate(Base):
    """Device certificate model."""
    
    __tablename__ = "device_certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("pi_devices.id"), nullable=False, index=True)
    certificate_data = Column(Text, nullable=False)
    private_key = Column(Text, nullable=True)  # Encrypted private key
    fingerprint = Column(String(64), nullable=False, unique=True, index=True)
    issued_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    device = relationship("PiDevice")
