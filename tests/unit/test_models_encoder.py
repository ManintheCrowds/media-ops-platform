"""Unit tests for encoder models."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.encoder.encoder_models import VideoEncoder
from app.models.encoder.enums import EncoderStatus, EncoderDeviceType


@pytest.mark.unit
class TestVideoEncoder:
    """Test VideoEncoder model."""
    
    def test_create_encoder(self, db_session):
        """Test creating an encoder."""
        encoder = VideoEncoder(
            name="AJA HELO 1",
            ip_address="192.168.1.100",
            device_type=EncoderDeviceType.AJA_HELO,
            status=EncoderStatus.ONLINE,
            port=80,
            is_recording=False,
            is_streaming=False
        )
        db_session.add(encoder)
        db_session.commit()
        
        assert encoder.id is not None
        assert encoder.name == "AJA HELO 1"
        assert encoder.ip_address == "192.168.1.100"
        assert encoder.device_type == EncoderDeviceType.AJA_HELO
        assert encoder.status == EncoderStatus.ONLINE
        assert encoder.port == 80
        assert encoder.is_recording is False
        assert encoder.is_streaming is False
        assert encoder.created_at is not None
        assert encoder.updated_at is None
    
    def test_encoder_defaults(self, db_session):
        """Test encoder default values."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.101"
        )
        db_session.add(encoder)
        db_session.commit()
        
        assert encoder.device_type == EncoderDeviceType.AJA_HELO  # Default
        assert encoder.status == EncoderStatus.UNKNOWN  # Default
        assert encoder.is_recording is False  # Default
        assert encoder.is_streaming is False  # Default
        assert encoder.port == 80  # Default
        assert encoder.current_recording_path is None
        assert encoder.current_stream_url is None
        assert encoder.storage_available is None
        assert encoder.storage_used is None
    
    def test_encoder_unique_ip_address(self, db_session):
        """Test that IP addresses must be unique."""
        encoder1 = VideoEncoder(
            name="Encoder 1",
            ip_address="192.168.1.100"
        )
        db_session.add(encoder1)
        db_session.commit()
        
        encoder2 = VideoEncoder(
            name="Encoder 2",
            ip_address="192.168.1.100"  # Duplicate
        )
        db_session.add(encoder2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_encoder_to_dict(self, db_session):
        """Test encoder serialization."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.102",
            device_type=EncoderDeviceType.AJA_HELO,
            status=EncoderStatus.ONLINE,
            is_recording=True,
            current_recording_path="/path/to/recording.mp4",
            storage_available=1000000000,
            storage_used=500000000
        )
        db_session.add(encoder)
        db_session.commit()
        
        data = encoder.to_dict()
        
        assert data['id'] == encoder.id
        assert data['name'] == "Test Encoder"
        assert data['ip_address'] == "192.168.1.102"
        assert data['device_type'] == "aja_helo"
        assert data['status'] == "online"
        assert data['is_recording'] is True
        assert data['current_recording_path'] == "/path/to/recording.mp4"
        assert data['storage_available'] == 1000000000
        assert data['storage_used'] == 500000000
        assert data['port'] == 80
        assert 'created_at' in data
        assert 'updated_at' in data
    
    def test_encoder_with_all_fields(self, db_session):
        """Test encoder with all optional fields."""
        encoder = VideoEncoder(
            name="Full Encoder",
            ip_address="192.168.1.103",
            device_type=EncoderDeviceType.AJA_HELO,
            status=EncoderStatus.RECORDING,
            is_recording=True,
            is_streaming=True,
            current_recording_path="/recordings/video.mp4",
            current_stream_url="rtmp://stream.example.com/live",
            storage_available=2000000000,
            storage_used=1500000000,
            port=8080
        )
        db_session.add(encoder)
        db_session.commit()
        
        assert encoder.is_recording is True
        assert encoder.is_streaming is True
        assert encoder.current_recording_path == "/recordings/video.mp4"
        assert encoder.current_stream_url == "rtmp://stream.example.com/live"
        assert encoder.storage_available == 2000000000
        assert encoder.storage_used == 1500000000
        assert encoder.port == 8080
    
    def test_encoder_status_enum(self, db_session):
        """Test encoder status enum values."""
        encoder = VideoEncoder(
            name="Status Test",
            ip_address="192.168.1.104",
            status=EncoderStatus.ERROR
        )
        db_session.add(encoder)
        db_session.commit()
        
        assert encoder.status == EncoderStatus.ERROR
        data = encoder.to_dict()
        assert data['status'] == "error"
    
    def test_encoder_device_type_enum(self, db_session):
        """Test encoder device type enum values."""
        encoder = VideoEncoder(
            name="Device Type Test",
            ip_address="192.168.1.105",
            device_type=EncoderDeviceType.GENERIC
        )
        db_session.add(encoder)
        db_session.commit()
        
        assert encoder.device_type == EncoderDeviceType.GENERIC
        data = encoder.to_dict()
        assert data['device_type'] == "generic"
    
    def test_encoder_storage_fields(self, db_session):
        """Test encoder storage fields with large values."""
        encoder = VideoEncoder(
            name="Storage Test",
            ip_address="192.168.1.106",
            storage_available=1099511627776,  # 1 TB in bytes
            storage_used=549755813888  # 512 GB in bytes
        )
        db_session.add(encoder)
        db_session.commit()
        
        assert encoder.storage_available == 1099511627776
        assert encoder.storage_used == 549755813888


@pytest.mark.unit
class TestEncoderEnums:
    """Test encoder enums."""
    
    def test_encoder_status_enum_values(self):
        """Test that EncoderStatus enum has expected values."""
        assert EncoderStatus.ONLINE.value == "online"
        assert EncoderStatus.OFFLINE.value == "offline"
        assert EncoderStatus.UNKNOWN.value == "unknown"
        assert EncoderStatus.ERROR.value == "error"
        assert EncoderStatus.RECORDING.value == "recording"
        assert EncoderStatus.STREAMING.value == "streaming"
    
    def test_encoder_device_type_enum_values(self):
        """Test that EncoderDeviceType enum has expected values."""
        assert EncoderDeviceType.AJA_HELO.value == "aja_helo"
        assert EncoderDeviceType.GENERIC.value == "generic"
    
    def test_encoder_enum_serialization(self, db_session):
        """Test that enum values serialize correctly in to_dict."""
        encoder = VideoEncoder(
            name="Enum Test",
            ip_address="192.168.1.107",
            status=EncoderStatus.STREAMING,
            device_type=EncoderDeviceType.AJA_HELO
        )
        db_session.add(encoder)
        db_session.commit()
        
        data = encoder.to_dict()
        assert data['status'] == "streaming"  # Should be string value
        assert data['device_type'] == "aja_helo"  # Should be string value

