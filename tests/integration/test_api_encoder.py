"""Integration tests for encoder API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status

from app.models.encoder.encoder_models import VideoEncoder
from app.models.encoder.enums import EncoderStatus, EncoderDeviceType


@pytest.mark.integration
class TestEncoderListGet:
    """Test encoder listing and retrieval endpoints."""
    
    def test_list_encoders_empty(self, client, test_token):
        """Test listing encoders when none exist."""
        response = client.get(
            "/api/encoder/encoders",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
    
    def test_list_encoders_with_data(self, client, test_token, db_session):
        """Test listing encoders with existing data."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            status=EncoderStatus.ONLINE
        )
        db_session.add(encoder)
        db_session.commit()
        
        response = client.get(
            "/api/encoder/encoders",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['name'] == "Test Encoder"
        assert data[0]['ip_address'] == "192.168.1.100"
    
    def test_get_encoder_success(self, client, test_token, db_session):
        """Test getting encoder by ID."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100"
        )
        db_session.add(encoder)
        db_session.commit()
        
        response = client.get(
            f"/api/encoder/encoders/{encoder.id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['id'] == encoder.id
        assert data['name'] == "Test Encoder"
    
    def test_get_encoder_not_found(self, client, test_token):
        """Test getting non-existent encoder."""
        response = client.get(
            "/api/encoder/encoders/999",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_list_encoders_requires_auth(self, client):
        """Test that listing encoders requires authentication."""
        response = client.get("/api/encoder/encoders")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
class TestEncoderDiscovery:
    """Test encoder discovery endpoint."""
    
    def test_discover_encoders_requires_admin(self, client, test_token):
        """Test that discovery requires admin access."""
        response = client.post(
            "/api/encoder/encoders/discover",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_discover_encoders_admin_success(self, client, admin_token):
        """Test successful encoder discovery by admin."""
        mock_discovered = [
            {
                'ip_address': '192.168.1.100',
                'port': 80,
                'device_type': 'aja_helo',
                'status': 'online',
                'device_info': {'name': 'AJA HELO'}
            }
        ]
        
        with patch('app.api.encoder.VideoEncoderService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.discover_encoders = AsyncMock(return_value=mock_discovered)
            
            response = client.post(
                "/api/encoder/encoders/discover?network_range=192.168.1.0/24",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['message'] == "Encoder discovery completed"
            assert len(data['discovered']) == 1
            assert data['discovered'][0]['ip_address'] == '192.168.1.100'


@pytest.mark.integration
class TestEncoderRegistration:
    """Test encoder registration endpoint."""
    
    def test_register_encoder_requires_admin(self, client, test_token):
        """Test that registration requires admin access."""
        response = client.post(
            "/api/encoder/encoders",
            json={
                "name": "Test Encoder",
                "ip_address": "192.168.1.100"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_register_encoder_admin_success(self, client, admin_token, db_session):
        """Test successful encoder registration by admin."""
        encoder_data = {
            "name": "Test Encoder",
            "ip_address": "192.168.1.100",
            "port": 80,
            "device_type": "AJA_HELO"
        }
        
        response = client.post(
            "/api/encoder/encoders",
            json=encoder_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['name'] == "Test Encoder"
        assert data['ip_address'] == "192.168.1.100"
        
        # Verify in database
        encoder = db_session.query(VideoEncoder).filter_by(ip_address="192.168.1.100").first()
        assert encoder is not None
    
    def test_register_encoder_missing_fields(self, client, admin_token):
        """Test registration fails with missing required fields."""
        response = client.post(
            "/api/encoder/encoders",
            json={
                "ip_address": "192.168.1.100"
                # Missing name
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.integration
class TestEncoderRecording:
    """Test encoder recording endpoints."""
    
    def test_start_recording_requires_admin(self, client, test_token):
        """Test that starting recording requires admin access."""
        response = client.post(
            "/api/encoder/encoders/1/record",
            json={
                "source_url": "rtmp://example.com/stream"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_start_recording_admin_success(self, client, admin_token, db_session):
        """Test successful recording start by admin."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            is_recording=False
        )
        db_session.add(encoder)
        db_session.commit()
        
        with patch('app.api.encoder.VideoEncoderService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.record_stream = AsyncMock(return_value={
                'status': 'recording',
                'encoder_id': encoder.id,
                'output_path': '/path/to/recording.mp4',
                'source_url': 'rtmp://example.com/stream'
            })
            
            response = client.post(
                f"/api/encoder/encoders/{encoder.id}/record",
                json={
                    "source_url": "rtmp://example.com/stream",
                    "duration": 60
                },
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['status'] == 'recording'
            assert data['encoder_id'] == encoder.id
    
    def test_stop_recording_requires_admin(self, client, test_token):
        """Test that stopping recording requires admin access."""
        response = client.post(
            "/api/encoder/encoders/1/stop",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_stop_recording_admin_success(self, client, admin_token, db_session):
        """Test successful recording stop by admin."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            is_recording=True,
            status=EncoderStatus.RECORDING
        )
        db_session.add(encoder)
        db_session.commit()
        
        with patch('app.api.encoder.VideoEncoderService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.stop_recording = AsyncMock(return_value={
                'status': 'stopped',
                'encoder_id': encoder.id,
                'recording_path': '/path/to/recording.mp4'
            })
            
            response = client.post(
                f"/api/encoder/encoders/{encoder.id}/stop",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['status'] == 'stopped'
            assert data['encoder_id'] == encoder.id


@pytest.mark.integration
class TestEncoderStatus:
    """Test encoder status endpoint."""
    
    def test_get_encoder_status_success(self, client, test_token, db_session):
        """Test getting encoder status."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            status=EncoderStatus.ONLINE
        )
        db_session.add(encoder)
        db_session.commit()
        
        with patch('app.api.encoder.VideoEncoderService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_encoder_status = AsyncMock(return_value={
                'encoder_id': encoder.id,
                'status': 'online',
                'is_recording': False,
                'is_streaming': False,
                'device_status': {'status': 'online'}
            })
            
            response = client.get(
                f"/api/encoder/encoders/{encoder.id}/status",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['encoder_id'] == encoder.id
            assert data['status'] == 'online'


@pytest.mark.integration
class TestCameraEncoderIntegration:
    """Test camera-encoder integration endpoint."""
    
    def test_record_camera_requires_admin(self, client, test_token):
        """Test that recording camera requires admin access."""
        response = client.post(
            "/api/encoder/cameras/1/record?encoder_id=1",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_record_camera_admin_success(self, client, admin_token, db_session):
        """Test successful camera recording via encoder."""
        from app.models.camera.arlo_models import ArloBaseStation, ArloCamera
        from app.models.camera.enums import ArloStatus
        
        # Create camera
        station = ArloBaseStation(name="Base", serial_number="BS001")
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Test Camera",
            device_id="CAM001"
        )
        db_session.add(camera)
        db_session.flush()
        
        # Create encoder
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            is_recording=False
        )
        db_session.add(encoder)
        db_session.commit()
        
        with patch('app.api.encoder.CameraRecordingService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.record_camera = AsyncMock(return_value={
                'status': 'recording',
                'encoder_id': encoder.id,
                'camera_id': camera.id,
                'output_path': '/path/to/recording.mp4'
            })
            
            response = client.post(
                f"/api/encoder/cameras/{camera.id}/record?encoder_id={encoder.id}&duration=3600",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['status'] == 'recording'
            assert data['encoder_id'] == encoder.id
    
    def test_record_camera_missing_encoder_id(self, client, admin_token):
        """Test recording camera fails without encoder_id parameter."""
        response = client.post(
            "/api/encoder/cameras/1/record",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should fail validation (encoder_id is required query param)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

