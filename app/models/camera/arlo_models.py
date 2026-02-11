"""Arlo camera database models."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, JSON, Index, BigInteger
from sqlalchemy.orm import relationship
from app.models import Base
from .mixins import TimestampMixin
from .enums import ArloStatus, ArloEventType


class ArloBaseStation(Base, TimestampMixin):
    """Arlo base station model."""
    __tablename__ = 'arlo_base_stations'

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    serial_number = Column(String(64), unique=True, nullable=False, index=True)
    ip_address = Column(String(15))
    status = Column(Enum(ArloStatus), default=ArloStatus.UNKNOWN)
    last_sync = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    credentials_encrypted = Column(String(512))  # Encrypted Arlo credentials

    # Relationships
    cameras = relationship('ArloCamera', back_populates='base_station', cascade='all, delete-orphan')

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'serial_number': self.serial_number,
            'ip_address': self.ip_address,
            'status': self.status.value if self.status else None,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'camera_count': len(self.cameras) if self.cameras else 0
        }


class ArloCamera(Base, TimestampMixin):
    """Arlo camera model."""
    __tablename__ = 'arlo_cameras'

    id = Column(Integer, primary_key=True)
    base_station_id = Column(Integer, ForeignKey('arlo_base_stations.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(64), nullable=False)
    device_id = Column(String(64), unique=True, nullable=False, index=True)
    device_type = Column(String(32))  # e.g., 'arloq', 'arlopro', etc.
    status = Column(Enum(ArloStatus), default=ArloStatus.UNKNOWN, index=True)
    is_armed = Column(Boolean, default=False)
    battery_level = Column(Integer)  # 0-100
    signal_strength = Column(Integer)  # Signal strength percentage

    # Relationships
    base_station = relationship('ArloBaseStation', back_populates='cameras')
    recordings = relationship('ArloRecording', back_populates='camera', cascade='all, delete-orphan')
    events = relationship('ArloEvent', back_populates='camera', cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        Index('idx_arlo_camera_base_station', 'base_station_id'),
        Index('idx_arlo_camera_device_id', 'device_id'),
        Index('idx_arlo_camera_status', 'status'),
    )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'base_station_id': self.base_station_id,
            'name': self.name,
            'device_id': self.device_id,
            'device_type': self.device_type,
            'status': self.status.value if self.status else None,
            'is_armed': self.is_armed,
            'battery_level': self.battery_level,
            'signal_strength': self.signal_strength,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ArloRecording(Base, TimestampMixin):
    """Arlo recording model."""
    __tablename__ = 'arlo_recordings'

    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('arlo_cameras.id', ondelete='CASCADE'), nullable=False, index=True)
    recording_id = Column(String(128), unique=True, nullable=False, index=True)  # Arlo cloud recording ID
    presigned_url = Column(String(512))  # Presigned URL for download
    created_date = Column(DateTime(timezone=True), nullable=False, index=True)
    duration = Column(Integer)  # Duration in seconds
    file_size = Column(BigInteger)  # File size in bytes
    downloaded = Column(Boolean, default=False)  # Whether recording has been downloaded locally

    # Relationships
    camera = relationship('ArloCamera', back_populates='recordings')

    # Indexes
    __table_args__ = (
        Index('idx_arlo_recording_camera', 'camera_id'),
        Index('idx_arlo_recording_id', 'recording_id'),
        Index('idx_arlo_recording_date', 'created_date'),
    )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'recording_id': self.recording_id,
            'presigned_url': self.presigned_url,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'duration': self.duration,
            'file_size': self.file_size,
            'downloaded': self.downloaded,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ArloEvent(Base, TimestampMixin):
    """Arlo event model for motion/activity events."""
    __tablename__ = 'arlo_events'

    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('arlo_cameras.id', ondelete='CASCADE'), nullable=False, index=True)
    event_type = Column(Enum(ArloEventType), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    details = Column(JSON)  # Additional event details (JSON)

    # Relationships
    camera = relationship('ArloCamera', back_populates='events')

    # Indexes
    __table_args__ = (
        Index('idx_arlo_event_camera', 'camera_id'),
        Index('idx_arlo_event_type', 'event_type'),
        Index('idx_arlo_event_timestamp', 'timestamp'),
    )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'event_type': self.event_type.value if self.event_type else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

