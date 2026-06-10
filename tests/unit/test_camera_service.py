"""Unit tests for Arlo camera service with mocked dependencies."""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path

from services.camera.arlo_service import ArloService
from services.camera.config import CameraConfig
from app.models.camera.arlo_models import ArloBaseStation, ArloCamera, ArloRecording
from app.models.camera.enums import ArloStatus
from app.exceptions import (
    ArloError,
    ArloConnectionError,
    ArloCameraError,
    ArloRecordingError
)


@pytest.fixture
def mock_arlo_client():
    """Create a mock Arlo client."""
    mock = MagicMock()
    mock.GetDevices.return_value = [
        {
            'deviceId': 'CAM001',
            'deviceType': 'arloq',
            'deviceName': 'Front Door',
            'state': 'provisioned',
            'properties': {
                'armed': True,
                'batteryLevel': 85,
                'signalStrength': 90
            }
        }
    ]
    mock.Arm.return_value = True
    mock.Disarm.return_value = True
    mock.TriggerFullFrameSnapshot.return_value = "https://example.com/snapshot.jpg"
    mock.GetLibrary.return_value = [
        {
            'name': 'recording1.mp4',
            'mediaDurationSecond': 30,
            'createdDate': '2024-01-01T00:00:00Z',
            'presignedContentUrl': 'https://example.com/video.mp4',
            'mediaSize': 1024000
        }
    ]
    mock.StartStream.return_value = "rtmp://stream.example.com/live"
    return mock


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock camera config."""
    storage_path = tmp_path / "recordings"
    config = CameraConfig(
        arlo_username="test@example.com",
        arlo_password="testpass",
        storage_path=str(storage_path)
    )
    return config


@pytest.fixture
def arlo_service(mock_config):
    """Create ArloService instance with mocked config."""
    with patch('services.camera.arlo_service.Arlo'):
        service = ArloService(config=mock_config)
        return service


@pytest.mark.unit
class TestArloServiceInit:
    """Test ArloService initialization."""
    
    def test_init_with_config(self, mock_config):
        """Test service initialization with config."""
        with patch('services.camera.arlo_service.Arlo'):
            service = ArloService(config=mock_config)
            
            assert service.config == mock_config
            assert service.storage_path.exists()
    
    def test_init_with_default_config(self):
        """Test service initialization with default config."""
        with patch('services.camera.arlo_service.Arlo'):
            service = ArloService()
            
            assert service.config is not None
            assert isinstance(service.config, CameraConfig)


@pytest.mark.unit
class TestArloServiceGetClient:
    """Test ArloService client management."""
    
    def test_get_client_success(self, arlo_service, mock_arlo_client):
        """Test getting Arlo client successfully."""
        with patch('services.camera.arlo_service.Arlo', return_value=mock_arlo_client):
            client = arlo_service._get_arlo_client("test@example.com", "password")
            
            assert client == mock_arlo_client
    
    def test_get_client_no_arlo_library(self, arlo_service):
        """Test error when Arlo library is not available."""
        with patch('services.camera.arlo_service.Arlo', None):
            with pytest.raises(ArloConnectionError) as exc_info:
                arlo_service._get_arlo_client()
            
            assert "Arlo library not installed" in str(exc_info.value)
    
    def test_get_client_no_credentials(self, arlo_service):
        """Test error when credentials are missing."""
        arlo_service.config.arlo_username = None
        arlo_service.config.arlo_password = None
        
        with patch('services.camera.arlo_service.Arlo'):
            with pytest.raises(ArloConnectionError) as exc_info:
                arlo_service._get_arlo_client()
            
            assert "Arlo credentials not configured" in str(exc_info.value)
    
    def test_get_client_caches_instance(self, arlo_service, mock_arlo_client):
        """Test that client instances are cached."""
        with patch('services.camera.arlo_service.Arlo', return_value=mock_arlo_client):
            client1 = arlo_service._get_arlo_client("user@example.com", "pass")
            client2 = arlo_service._get_arlo_client("user@example.com", "pass")
            
            assert client1 == client2
            assert len(arlo_service._clients) == 1


@pytest.mark.unit
class TestArloServiceDiscover:
    """Test camera discovery."""
    
    @pytest.mark.asyncio
    async def test_discover_cameras_success(self, arlo_service, db_session, mock_arlo_client):
        """Test successful camera discovery."""
        with patch.object(arlo_service, '_get_arlo_client', return_value=mock_arlo_client):
            cameras = await arlo_service.discover_cameras(db_session)
            
            assert len(cameras) == 1
            assert cameras[0]['device_id'] == 'CAM001'
            assert cameras[0]['device_type'] == 'arloq'
            assert cameras[0]['name'] == 'Front Door'
            assert cameras[0]['status'] == 'online'
    
    @pytest.mark.asyncio
    async def test_discover_cameras_filters_by_type(self, arlo_service, db_session, mock_arlo_client):
        """Test that discovery filters by device type."""
        mock_arlo_client.GetDevices.return_value = [
            {'deviceId': 'CAM001', 'deviceType': 'arloq', 'deviceName': 'Camera 1', 'state': 'provisioned', 'properties': {}},
            {'deviceId': 'BS001', 'deviceType': 'basestation', 'deviceName': 'Base', 'state': 'provisioned', 'properties': {}},
            {'deviceId': 'CAM002', 'deviceType': 'arlopro', 'deviceName': 'Camera 2', 'state': 'provisioned', 'properties': {}}
        ]
        
        with patch.object(arlo_service, '_get_arlo_client', return_value=mock_arlo_client):
            cameras = await arlo_service.discover_cameras(db_session)
            
            assert len(cameras) == 2  # Only cameras, not base station
            assert all(cam['device_type'] in ['arloq', 'arlopro'] for cam in cameras)
    
    @pytest.mark.asyncio
    async def test_discover_cameras_connection_error(self, arlo_service, db_session):
        """Test discovery raises error on connection failure."""
        mock_client = MagicMock()
        mock_client.GetDevices.side_effect = Exception("Connection failed")
        
        with patch.object(arlo_service, '_get_arlo_client', return_value=mock_client):
            with pytest.raises(ArloConnectionError) as exc_info:
                await arlo_service.discover_cameras(db_session)
            
            assert "Failed to discover cameras" in str(exc_info.value)


@pytest.mark.unit
class TestArloServiceRegister:
    """Test camera registration."""
    
    @pytest.mark.asyncio
    async def test_register_camera_new(self, arlo_service, db_session):
        """Test registering a new camera."""
        camera_data = {
            'device_id': 'CAM123',
            'device_type': 'arloq',
            'name': 'Test Camera',
            'status': 'ONLINE'
        }
        
        result = await arlo_service.register_camera(db_session, camera_data)
        
        assert result['device_id'] == 'CAM123'
        assert result['name'] == 'Test Camera'
        
        # Verify in database
        camera = db_session.query(ArloCamera).filter_by(device_id='CAM123').first()
        assert camera is not None
        assert camera.name == 'Test Camera'
    
    @pytest.mark.asyncio
    async def test_register_camera_existing(self, arlo_service, db_session):
        """Test updating an existing camera."""
        # Create base station and camera
        station = ArloBaseStation(name="Base", serial_number="BS001")
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Old Name",
            device_id="CAM123",
            status=ArloStatus.OFFLINE
        )
        db_session.add(camera)
        db_session.commit()
        
        # Update camera
        camera_data = {
            'device_id': 'CAM123',
            'device_type': 'arloq',
            'name': 'New Name',
            'status': 'ONLINE'
        }
        
        result = await arlo_service.register_camera(db_session, camera_data)
        
        assert result['name'] == 'New Name'
        assert result['status'] == 'online'
        
        # Verify update
        db_session.refresh(camera)
        assert camera.name == 'New Name'
        assert camera.status == ArloStatus.ONLINE
    
    @pytest.mark.asyncio
    async def test_register_camera_missing_fields(self, arlo_service, db_session):
        """Test registration fails with missing required fields."""
        camera_data = {
            'device_id': 'CAM123'
            # Missing name and device_type
        }
        
        with pytest.raises(ArloError) as exc_info:
            await arlo_service.register_camera(db_session, camera_data)
        
        assert "Missing required field" in str(exc_info.value)


@pytest.mark.unit
class TestArloServiceListGet:
    """Test listing and getting cameras."""
    
    @pytest.mark.asyncio
    async def test_list_cameras(self, arlo_service, db_session):
        """Test listing all cameras."""
        # Create test data
        station = ArloBaseStation(name="Base", serial_number="BS001")
        db_session.add(station)
        db_session.flush()
        
        camera1 = ArloCamera(
            base_station_id=station.id,
            name="Camera 1",
            device_id="CAM001"
        )
        camera2 = ArloCamera(
            base_station_id=station.id,
            name="Camera 2",
            device_id="CAM002"
        )
        db_session.add_all([camera1, camera2])
        db_session.commit()
        
        cameras = await arlo_service.list_cameras(db_session)
        
        assert len(cameras) == 2
        assert all('id' in cam for cam in cameras)
        assert all('name' in cam for cam in cameras)
    
    @pytest.mark.asyncio
    async def test_get_camera_success(self, arlo_service, db_session):
        """Test getting camera by ID."""
        station = ArloBaseStation(name="Base", serial_number="BS001")
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Test Camera",
            device_id="CAM001"
        )
        db_session.add(camera)
        db_session.commit()
        
        result = await arlo_service.get_camera(db_session, camera.id)
        
        assert result['id'] == camera.id
        assert result['name'] == 'Test Camera'
    
    @pytest.mark.asyncio
    async def test_get_camera_not_found(self, arlo_service, db_session):
        """Test getting non-existent camera raises error."""
        with pytest.raises(ArloCameraError) as exc_info:
            await arlo_service.get_camera(db_session, 999)
        
        assert "Camera not found" in str(exc_info.value)


@pytest.mark.unit
class TestArloServiceArmDisarm:
    """Test camera arming/disarming."""
    
    @pytest.mark.asyncio
    async def test_arm_camera_success(self, arlo_service, db_session, mock_arlo_client):
        """Test successfully arming a camera."""
        station = ArloBaseStation(name="Base", serial_number="BS001")
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Test Camera",
            device_id="CAM001",
            is_armed=False
        )
        db_session.add(camera)
        db_session.commit()
        
        with patch.object(arlo_service, '_get_arlo_client', return_value=mock_arlo_client):
            result = await arlo_service.arm_camera(db_session, camera.id)
            
            assert result['is_armed'] is True
            mock_arlo_client.Arm.assert_called_once_with("CAM001")
    
    @pytest.mark.asyncio
    async def test_disarm_camera_success(self, arlo_service, db_session, mock_arlo_client):
        """Test successfully disarming a camera."""
        station = ArloBaseStation(name="Base", serial_number="BS001")
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Test Camera",
            device_id="CAM001",
            is_armed=True
        )
        db_session.add(camera)
        db_session.commit()
        
        with patch.object(arlo_service, '_get_arlo_client', return_value=mock_arlo_client):
            result = await arlo_service.disarm_camera(db_session, camera.id)
            
            assert result['is_armed'] is False
            mock_arlo_client.Disarm.assert_called_once_with("CAM001")
    
    @pytest.mark.asyncio
    async def test_arm_camera_not_found(self, arlo_service, db_session):
        """Test arming non-existent camera raises error."""
        with pytest.raises(ArloCameraError):
            await arlo_service.arm_camera(db_session, 999)
    
    @pytest.mark.asyncio
    async def test_arm_camera_client_error(self, arlo_service, db_session, mock_arlo_client):
        """Test arming camera handles client errors."""
        station = ArloBaseStation(name="Base", serial_number="BS001")
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Test Camera",
            device_id="CAM001"
        )
        db_session.add(camera)
        db_session.commit()
        
        mock_arlo_client.Arm.side_effect = Exception("Arm failed")
        
        with patch.object(arlo_service, '_get_arlo_client', return_value=mock_arlo_client):
            with pytest.raises(ArloCameraError) as exc_info:
                await arlo_service.arm_camera(db_session, camera.id)
            
            assert "Failed to arm camera" in str(exc_info.value)


@pytest.mark.unit
class TestArloServiceSnapshot:
    """Test snapshot capture."""
    
    @pytest.mark.asyncio
    async def test_capture_snapshot_success(self, arlo_service, db_session, mock_arlo_client):
        """Test successfully capturing snapshot."""
        station = ArloBaseStation(name="Base", serial_number="BS001")
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Test Camera",
            device_id="CAM001"
        )
        db_session.add(camera)
        db_session.commit()
        
        with patch.object(arlo_service, '_get_arlo_client', return_value=mock_arlo_client):
            result = await arlo_service.capture_snapshot(db_session, camera.id)
            
            assert result['camera_id'] == camera.id
            assert 'snapshot_url' in result
            assert 'timestamp' in result
            mock_arlo_client.TriggerFullFrameSnapshot.assert_called_once_with("CAM001")
    
    @pytest.mark.asyncio
    async def test_capture_snapshot_not_found(self, arlo_service, db_session):
        """Test capturing snapshot from non-existent camera raises error."""
        with pytest.raises(ArloCameraError):
            await arlo_service.capture_snapshot(db_session, 999)

