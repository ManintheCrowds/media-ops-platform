"""Video encoder database models."""

from sqlalchemy import Column, Integer, String, Boolean, BigInteger, Enum, Index
from app.models import Base
from app.models.camera.mixins import TimestampMixin
from .enums import EncoderStatus, EncoderDeviceType


class VideoEncoder(Base, TimestampMixin):
    """Video encoder device model."""
    __tablename__ = 'video_encoders'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    ip_address = Column(String(15), unique=True, nullable=False, index=True)
    device_type = Column(Enum(EncoderDeviceType), default=EncoderDeviceType.AJA_HELO, index=True)
    status = Column(Enum(EncoderStatus), default=EncoderStatus.UNKNOWN, index=True)
    is_recording = Column(Boolean, default=False)
    is_streaming = Column(Boolean, default=False)
    current_recording_path = Column(String(512))
    current_stream_url = Column(String(512))
    storage_available = Column(BigInteger)  # bytes
    storage_used = Column(BigInteger)  # bytes
    port = Column(Integer, default=80)
    
    # Indexes
    __table_args__ = (
        Index('idx_encoder_ip_address', 'ip_address'),
        Index('idx_encoder_status', 'status'),
        Index('idx_encoder_device_type', 'device_type'),
    )
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'ip_address': self.ip_address,
            'device_type': self.device_type.value if self.device_type else None,
            'status': self.status.value if self.status else None,
            'is_recording': self.is_recording,
            'is_streaming': self.is_streaming,
            'current_recording_path': self.current_recording_path,
            'current_stream_url': self.current_stream_url,
            'storage_available': self.storage_available,
            'storage_used': self.storage_used,
            'port': self.port,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

