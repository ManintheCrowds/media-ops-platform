"""Integration tests for camera API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status

from app.models.camera.arlo_models import ArloBaseStation, ArloCamera
from app.models.camera.enums import ArloStatus


@pytest.mark.integration
class TestCameraListGet:
    """Test camera listing and retrieval endpoints."""
    
    def test_list_cameras_empty(self, client, test_token):
        """Test listing cameras when none exist."""
        response = client.get(
            "/api/camera/cameras",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
    
    def test_list_cameras_with_data(self, client, test_token, db_session):
        """Test listing cameras with existing data."""
        # Create test data
        station = ArloBaseStation(name="Base", serial_number="BS001")
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Test Camera",
            device_id="CAM001",
            status=ArloStatus.ONLINE
        )
        db_session.add(camera)
        db_session.commit()
        
        response = client.get(
            "/api/camera/cameras",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['name'] == "Test Camera"
        assert data[0]['device_id'] == "CAM001"
    
    def test_get_camera_success(self, client, test_token, db_session):
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
        
        response = client.get(
            f"/api/camera/cameras/{camera.id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['id'] == camera.id
        assert data['name'] == "Test Camera"
    
    def test_get_camera_not_found(self, client, test_token):
        """Test getting non-existent camera."""
        response = client.get(
            "/api/camera/cameras/999",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_list_cameras_requires_auth(self, client):
        """Test that listing cameras requires authentication."""
        response = client.get("/api/camera/cameras")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
class TestCameraDiscovery:
    """Test camera discovery endpoint."""
    
    def test_discover_cameras_requires_admin(self, client, test_token):
        """Test that discovery requires admin access."""
        response = client.post(
            "/api/camera/cameras/discover",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        # Non-admin user should get 403
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_discover_cameras_admin_success(self, client, admin_token, db_session):
        """Test successful camera discovery by admin."""
        mock_discovered = [
            {
                'device_id': 'CAM001',
                'device_type': 'arloq',
                'name': 'Front Door',
                'status': 'online',
                'is_armed': False
            }
        ]
        
        with patch('app.api.camera.ArloService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.discover_cameras = AsyncMock(return_value=mock_discovered)
            mock_service.register_camera = AsyncMock(return_value={
                'id': 1,
                'device_id': 'CAM001',
                'name': 'Front Door',
                'status': 'online'
            })
            
            response = client.post(
                "/api/camera/cameras/discover",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]['device_id'] == 'CAM001'
    
    def test_discover_cameras_connection_error(self, client, admin_token):
        """Test discovery handles connection errors."""
        from app.exceptions import ArloConnectionError
        
        with patch('app.api.camera.ArloService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.discover_cameras = AsyncMock(
                side_effect=ArloConnectionError("Connection failed")
            )
            
            response = client.post(
                "/api/camera/cameras/discover",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


@pytest.mark.integration
class TestCameraArmDisarm:
    """Test camera arming/disarming endpoints."""
    
    def test_arm_camera_requires_admin(self, client, test_token):
        """Test that arming requires admin access."""
        response = client.post(
            "/api/camera/cameras/1/arm",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_arm_camera_admin_success(self, client, admin_token, db_session):
        """Test successful camera arming by admin."""
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
        
        with patch('app.api.camera.ArloService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.arm_camera = AsyncMock(return_value={
                'id': camera.id,
                'name': 'Test Camera',
                'device_id': 'CAM001',
                'is_armed': True
            })
            
            response = client.post(
                f"/api/camera/cameras/{camera.id}/arm",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['is_armed'] is True
    
    def test_disarm_camera_admin_success(self, client, admin_token, db_session):
        """Test successful camera disarming by admin."""
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
        
        with patch('app.api.camera.ArloService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.disarm_camera = AsyncMock(return_value={
                'id': camera.id,
                'name': 'Test Camera',
                'device_id': 'CAM001',
                'is_armed': False
            })
            
            response = client.post(
                f"/api/camera/cameras/{camera.id}/disarm",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['is_armed'] is False


@pytest.mark.integration
class TestCameraSnapshot:
    """Test camera snapshot endpoint."""
    
    def test_capture_snapshot_requires_admin(self, client, test_token):
        """Test that snapshot requires admin access."""
        response = client.post(
            "/api/camera/cameras/1/snapshot",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_capture_snapshot_success(self, client, admin_token, db_session):
        """Test successful snapshot capture."""
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
        
        with patch('app.api.camera.ArloService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.capture_snapshot = AsyncMock(return_value={
                'camera_id': camera.id,
                'snapshot_url': 'https://example.com/snapshot.jpg',
                'timestamp': '2024-01-01T00:00:00'
            })
            
            response = client.post(
                f"/api/camera/cameras/{camera.id}/snapshot",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['camera_id'] == camera.id
            assert 'snapshot_url' in data


@pytest.mark.integration
class TestCameraStatus:
    """Test camera status endpoint."""
    
    def test_get_camera_status_success(self, client, test_token, db_session):
        """Test getting camera status."""
        station = ArloBaseStation(name="Base", serial_number="BS001")
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Test Camera",
            device_id="CAM001",
            status=ArloStatus.ONLINE
        )
        db_session.add(camera)
        db_session.commit()
        
        with patch('app.api.camera.ArloService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_camera_status = AsyncMock(return_value={
                'camera_id': camera.id,
                'status': 'online',
                'is_armed': False,
                'battery_level': 85
            })
            
            response = client.get(
                f"/api/camera/cameras/{camera.id}/status",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['camera_id'] == camera.id
            assert data['status'] == 'online'


@pytest.mark.integration
class TestCameraRecordings:
    """Test camera recordings endpoints."""
    
    def test_get_recordings_empty(self, client, test_token, db_session):
        """Test getting recordings when none exist."""
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
        
        with patch('app.api.camera.ArloService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_library = AsyncMock(return_value=[])
            
            response = client.get(
                f"/api/camera/cameras/{camera.id}/recordings",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            assert response.json() == []
    
    def test_get_recordings_with_data(self, client, test_token, db_session):
        """Test getting recordings with data."""
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
        
        mock_recordings = [
            {
                'id': 1,
                'camera_id': camera.id,
                'recording_id': 'REC001',
                'created_date': '2024-01-01T00:00:00',
                'duration': 30
            }
        ]
        
        with patch('app.api.camera.ArloService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_library = AsyncMock(return_value=mock_recordings)
            
            response = client.get(
                f"/api/camera/cameras/{camera.id}/recordings",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]['recording_id'] == 'REC001'


@pytest.mark.integration
class TestBaseStation:
    """Test base station endpoint."""
    
    def test_get_base_station_success(self, client, test_token, db_session):
        """Test getting base station info."""
        station = ArloBaseStation(
            name="Test Base",
            serial_number="BS001",
            status=ArloStatus.ONLINE
        )
        db_session.add(station)
        db_session.commit()
        
        with patch('app.api.camera.ArloService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_base_station = AsyncMock(return_value={
                'id': station.id,
                'name': 'Test Base',
                'serial_number': 'BS001',
                'camera_count': 0
            })
            
            response = client.get(
                "/api/camera/base-station",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['name'] == 'Test Base'
            assert data['serial_number'] == 'BS001'


@pytest.mark.integration
class TestLiveStream:
    """Test live stream endpoint."""
    
    def test_start_live_stream_requires_admin(self, client, test_token):
        """Test that starting stream requires admin access."""
        response = client.post(
            "/api/camera/cameras/1/live-stream",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_start_live_stream_success(self, client, admin_token, db_session):
        """Test successful live stream start."""
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
        
        with patch('app.api.camera.ArloService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.start_live_stream = AsyncMock(return_value={
                'camera_id': camera.id,
                'stream_url': 'rtmp://stream.example.com/live',
                'status': 'streaming'
            })
            
            response = client.post(
                f"/api/camera/cameras/{camera.id}/live-stream",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['camera_id'] == camera.id
            assert 'stream_url' in data

