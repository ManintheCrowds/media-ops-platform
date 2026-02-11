"""Unit tests for Arlo camera models."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.models.camera.arlo_models import (
    ArloBaseStation,
    ArloCamera,
    ArloRecording,
    ArloEvent
)
from app.models.camera.enums import ArloStatus, ArloEventType


@pytest.mark.unit
class TestArloBaseStation:
    """Test ArloBaseStation model."""
    
    def test_create_base_station(self, db_session):
        """Test creating a base station."""
        station = ArloBaseStation(
            name="Test Base Station",
            serial_number="BS123456",
            ip_address="192.168.1.100",
            status=ArloStatus.ONLINE
        )
        db_session.add(station)
        db_session.commit()
        
        assert station.id is not None
        assert station.name == "Test Base Station"
        assert station.serial_number == "BS123456"
        assert station.ip_address == "192.168.1.100"
        assert station.status == ArloStatus.ONLINE
        assert station.created_at is not None
        assert station.updated_at is None
    
    def test_base_station_defaults(self, db_session):
        """Test base station default values."""
        station = ArloBaseStation(
            name="Test Base",
            serial_number="BS789"
        )
        db_session.add(station)
        db_session.commit()
        
        assert station.status == ArloStatus.UNKNOWN  # Default
        assert station.last_sync is not None
        assert station.credentials_encrypted is None
    
    def test_base_station_unique_serial(self, db_session):
        """Test that serial numbers must be unique."""
        station1 = ArloBaseStation(
            name="Station 1",
            serial_number="BS123"
        )
        db_session.add(station1)
        db_session.commit()
        
        station2 = ArloBaseStation(
            name="Station 2",
            serial_number="BS123"  # Duplicate
        )
        db_session.add(station2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_base_station_to_dict(self, db_session):
        """Test base station serialization."""
        station = ArloBaseStation(
            name="Test Base",
            serial_number="BS999",
            status=ArloStatus.ONLINE
        )
        db_session.add(station)
        db_session.commit()
        
        data = station.to_dict()
        
        assert data['id'] == station.id
        assert data['name'] == "Test Base"
        assert data['serial_number'] == "BS999"
        assert data['status'] == "online"
        assert 'created_at' in data
        assert 'updated_at' in data
        assert data['camera_count'] == 0
    
    def test_base_station_camera_relationship(self, db_session):
        """Test base station to camera relationship."""
        station = ArloBaseStation(
            name="Test Base",
            serial_number="BS456"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Test Camera",
            device_id="CAM123",
            status=ArloStatus.ONLINE
        )
        db_session.add(camera)
        db_session.commit()
        
        assert len(station.cameras) == 1
        assert station.cameras[0].device_id == "CAM123"
        assert station.to_dict()['camera_count'] == 1


@pytest.mark.unit
class TestArloCamera:
    """Test ArloCamera model."""
    
    def test_create_camera(self, db_session):
        """Test creating a camera."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS001"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Front Door",
            device_id="CAM001",
            device_type="arloq",
            status=ArloStatus.ONLINE,
            is_armed=True,
            battery_level=85,
            signal_strength=90
        )
        db_session.add(camera)
        db_session.commit()
        
        assert camera.id is not None
        assert camera.name == "Front Door"
        assert camera.device_id == "CAM001"
        assert camera.device_type == "arloq"
        assert camera.status == ArloStatus.ONLINE
        assert camera.is_armed is True
        assert camera.battery_level == 85
        assert camera.signal_strength == 90
    
    def test_camera_defaults(self, db_session):
        """Test camera default values."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS002"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Camera",
            device_id="CAM002"
        )
        db_session.add(camera)
        db_session.commit()
        
        assert camera.status == ArloStatus.UNKNOWN  # Default
        assert camera.is_armed is False  # Default
        assert camera.battery_level is None
        assert camera.signal_strength is None
    
    def test_camera_unique_device_id(self, db_session):
        """Test that device IDs must be unique."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS003"
        )
        db_session.add(station)
        db_session.flush()
        
        camera1 = ArloCamera(
            base_station_id=station.id,
            name="Camera 1",
            device_id="CAM123"
        )
        db_session.add(camera1)
        db_session.commit()
        
        camera2 = ArloCamera(
            base_station_id=station.id,
            name="Camera 2",
            device_id="CAM123"  # Duplicate
        )
        db_session.add(camera2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_camera_to_dict(self, db_session):
        """Test camera serialization."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS004"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Test Camera",
            device_id="CAM004",
            status=ArloStatus.ONLINE
        )
        db_session.add(camera)
        db_session.commit()
        
        data = camera.to_dict()
        
        assert data['id'] == camera.id
        assert data['base_station_id'] == station.id
        assert data['name'] == "Test Camera"
        assert data['device_id'] == "CAM004"
        assert data['status'] == "online"
        assert 'created_at' in data
        assert 'updated_at' in data
    
    def test_camera_base_station_relationship(self, db_session):
        """Test camera to base station relationship."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS005"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Camera",
            device_id="CAM005"
        )
        db_session.add(camera)
        db_session.commit()
        
        assert camera.base_station.id == station.id
        assert camera.base_station.name == "Base"
    
    def test_camera_cascade_delete(self, db_session):
        """Test that cameras are deleted when base station is deleted."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS006"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Camera",
            device_id="CAM006"
        )
        db_session.add(camera)
        db_session.commit()
        
        camera_id = camera.id
        db_session.delete(station)
        db_session.commit()
        
        deleted_camera = db_session.query(ArloCamera).filter_by(id=camera_id).first()
        assert deleted_camera is None


@pytest.mark.unit
class TestArloRecording:
    """Test ArloRecording model."""
    
    def test_create_recording(self, db_session):
        """Test creating a recording."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS007"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Camera",
            device_id="CAM007"
        )
        db_session.add(camera)
        db_session.flush()
        
        recording = ArloRecording(
            camera_id=camera.id,
            recording_id="REC123",
            presigned_url="https://example.com/video.mp4",
            created_date=datetime.now(timezone.utc),
            duration=30,
            file_size=1024000,
            downloaded=False
        )
        db_session.add(recording)
        db_session.commit()
        
        assert recording.id is not None
        assert recording.recording_id == "REC123"
        assert recording.duration == 30
        assert recording.file_size == 1024000
        assert recording.downloaded is False
    
    def test_recording_defaults(self, db_session):
        """Test recording default values."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS008"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Camera",
            device_id="CAM008"
        )
        db_session.add(camera)
        db_session.flush()
        
        recording = ArloRecording(
            camera_id=camera.id,
            recording_id="REC456",
            created_date=datetime.now(timezone.utc)
        )
        db_session.add(recording)
        db_session.commit()
        
        assert recording.downloaded is False  # Default
        assert recording.presigned_url is None
        assert recording.duration is None
        assert recording.file_size is None
    
    def test_recording_unique_recording_id(self, db_session):
        """Test that recording IDs must be unique."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS009"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Camera",
            device_id="CAM009"
        )
        db_session.add(camera)
        db_session.flush()
        
        recording1 = ArloRecording(
            camera_id=camera.id,
            recording_id="REC789",
            created_date=datetime.now(timezone.utc)
        )
        db_session.add(recording1)
        db_session.commit()
        
        recording2 = ArloRecording(
            camera_id=camera.id,
            recording_id="REC789",  # Duplicate
            created_date=datetime.now(timezone.utc)
        )
        db_session.add(recording2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_recording_to_dict(self, db_session):
        """Test recording serialization."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS010"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Camera",
            device_id="CAM010"
        )
        db_session.add(camera)
        db_session.flush()
        
        created_date = datetime.now(timezone.utc)
        recording = ArloRecording(
            camera_id=camera.id,
            recording_id="REC010",
            created_date=created_date,
            duration=60
        )
        db_session.add(recording)
        db_session.commit()
        
        data = recording.to_dict()
        
        assert data['id'] == recording.id
        assert data['camera_id'] == camera.id
        assert data['recording_id'] == "REC010"
        assert data['duration'] == 60
        assert 'created_at' in data
        assert 'updated_at' in data
    
    def test_recording_camera_relationship(self, db_session):
        """Test recording to camera relationship."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS011"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Camera",
            device_id="CAM011"
        )
        db_session.add(camera)
        db_session.flush()
        
        recording = ArloRecording(
            camera_id=camera.id,
            recording_id="REC011",
            created_date=datetime.now(timezone.utc)
        )
        db_session.add(recording)
        db_session.commit()
        
        assert recording.camera.id == camera.id
        assert len(camera.recordings) == 1


@pytest.mark.unit
class TestArloEvent:
    """Test ArloEvent model."""
    
    def test_create_event(self, db_session):
        """Test creating an event."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS012"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Camera",
            device_id="CAM012"
        )
        db_session.add(camera)
        db_session.flush()
        
        event = ArloEvent(
            camera_id=camera.id,
            event_type=ArloEventType.MOTION,
            timestamp=datetime.now(timezone.utc),
            details={"zone": "front_door", "confidence": 0.95}
        )
        db_session.add(event)
        db_session.commit()
        
        assert event.id is not None
        assert event.event_type == ArloEventType.MOTION
        assert event.details["zone"] == "front_door"
        assert event.details["confidence"] == 0.95
    
    def test_event_default_timestamp(self, db_session):
        """Test event default timestamp."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS013"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Camera",
            device_id="CAM013"
        )
        db_session.add(camera)
        db_session.flush()
        
        event = ArloEvent(
            camera_id=camera.id,
            event_type=ArloEventType.MOTION
        )
        db_session.add(event)
        db_session.commit()
        
        assert event.timestamp is not None
    
    def test_event_to_dict(self, db_session):
        """Test event serialization."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS014"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Camera",
            device_id="CAM014"
        )
        db_session.add(camera)
        db_session.flush()
        
        event = ArloEvent(
            camera_id=camera.id,
            event_type=ArloEventType.MOTION,
            details={"test": "data"}
        )
        db_session.add(event)
        db_session.commit()
        
        data = event.to_dict()
        
        assert data['id'] == event.id
        assert data['camera_id'] == camera.id
        assert data['event_type'] == "motion"
        assert data['details'] == {"test": "data"}
        assert 'created_at' in data
        assert 'updated_at' in data
    
    def test_event_camera_relationship(self, db_session):
        """Test event to camera relationship."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS015"
        )
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Camera",
            device_id="CAM015"
        )
        db_session.add(camera)
        db_session.flush()
        
        event = ArloEvent(
            camera_id=camera.id,
            event_type=ArloEventType.MOTION
        )
        db_session.add(event)
        db_session.commit()
        
        assert event.camera.id == camera.id
        assert len(camera.events) == 1


@pytest.mark.unit
class TestModelEnums:
    """Test enum handling in models."""
    
    def test_status_enum_values(self):
        """Test that status enum has expected values."""
        assert ArloStatus.ONLINE.value == "online"
        assert ArloStatus.OFFLINE.value == "offline"
        assert ArloStatus.UNKNOWN.value == "unknown"
    
    def test_event_type_enum_values(self):
        """Test that event type enum has expected values."""
        assert ArloEventType.MOTION.value == "motion"
        assert ArloEventType.AUDIO.value == "audio"
    
    def test_model_with_enum_serialization(self, db_session):
        """Test that enum values serialize correctly."""
        station = ArloBaseStation(
            name="Base",
            serial_number="BS016",
            status=ArloStatus.ONLINE
        )
        db_session.add(station)
        db_session.commit()
        
        data = station.to_dict()
        assert data['status'] == "online"  # Should be string value, not enum object

