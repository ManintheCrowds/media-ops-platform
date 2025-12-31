"""Unit tests for error handling paths (invalid inputs, network failures)."""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from services.camera.arlo_service import ArloService
from services.video_encoder.encoder_service import VideoEncoderService
from app.exceptions import (
    ArloError,
    ArloConnectionError,
    ArloCameraError,
    EncoderError,
    EncoderConnectionError,
    EncoderRecordingError
)


@pytest.mark.unit
class TestArloServiceErrorPaths:
    """Test ArloService error handling."""
    
    @pytest.mark.asyncio
    async def test_discover_cameras_network_failure(self, db_session):
        """Test discovery handles network failures."""
        service = ArloService()
        mock_client = MagicMock()
        mock_client.GetDevices.side_effect = ConnectionError("Network unreachable")
        
        with patch.object(service, '_get_arlo_client', return_value=mock_client):
            with pytest.raises(ArloConnectionError) as exc_info:
                await service.discover_cameras(db_session)
            
            assert "Failed to discover cameras" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_register_camera_invalid_data(self, db_session):
        """Test registration with invalid camera data."""
        service = ArloService()
        
        # Missing required fields
        invalid_data = {'device_id': 'CAM001'}  # Missing name and device_type
        
        with pytest.raises(ArloError) as exc_info:
            await service.register_camera(db_session, invalid_data)
        
        assert "Missing required field" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_camera_invalid_id(self, db_session):
        """Test getting camera with invalid ID."""
        service = ArloService()
        
        with pytest.raises(ArloCameraError) as exc_info:
            await service.get_camera(db_session, -1)
        
        assert "Camera not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_arm_camera_timeout(self, db_session):
        """Test arming camera handles timeout errors."""
        service = ArloService()
        
        # Create test camera
        from app.models.camera.arlo_models import ArloBaseStation, ArloCamera
        from app.models.camera.enums import ArloStatus
        
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
        
        mock_client = MagicMock()
        mock_client.Arm.side_effect = TimeoutError("Request timed out")
        
        with patch.object(service, '_get_arlo_client', return_value=mock_client):
            with pytest.raises(ArloCameraError) as exc_info:
                await service.arm_camera(db_session, camera.id)
            
            assert "Failed to arm camera" in str(exc_info.value)


@pytest.mark.unit
class TestEncoderServiceErrorPaths:
    """Test VideoEncoderService error handling."""
    
    @pytest.mark.asyncio
    async def test_discover_encoders_network_failure(self, db_session):
        """Test discovery handles network failures."""
        service = VideoEncoderService()
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.side_effect = \
                ConnectionError("Network unreachable")
            
            # Should return empty list, not raise exception
            discovered = await service.discover_encoders(db_session)
            assert isinstance(discovered, list)
    
    @pytest.mark.asyncio
    async def test_register_encoder_invalid_data(self, db_session):
        """Test registration with invalid encoder data."""
        service = VideoEncoderService()
        
        # Missing required fields
        invalid_data = {'ip_address': '192.168.1.100'}  # Missing name
        
        with pytest.raises(EncoderError) as exc_info:
            await service.register_encoder(db_session, invalid_data)
        
        assert "Missing required field" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_record_stream_invalid_source_url(self, db_session):
        """Test recording with invalid source URL."""
        service = VideoEncoderService()
        
        from app.models.encoder.encoder_models import VideoEncoder
        
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            is_recording=False
        )
        db_session.add(encoder)
        db_session.commit()
        
        mock_client = AsyncMock()
        mock_client.configure_recording = AsyncMock()
        mock_client.start_recording.side_effect = Exception("Invalid source URL")
        
        with patch.object(service, '_get_encoder_client', return_value=mock_client):
            with pytest.raises(EncoderRecordingError) as exc_info:
                await service.record_stream(
                    db_session,
                    encoder.id,
                    source_url="invalid-url",
                    duration=60
                )
            
            assert "Failed to start recording" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_stop_recording_not_recording(self, db_session):
        """Test stopping recording when not recording."""
        service = VideoEncoderService()
        
        from app.models.encoder.encoder_models import VideoEncoder
        
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            is_recording=False
        )
        db_session.add(encoder)
        db_session.commit()
        
        with pytest.raises(EncoderRecordingError) as exc_info:
            await service.stop_recording(db_session, encoder.id)
        
        assert "not recording" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_encoder_status_connection_failure(self, db_session):
        """Test status check handles connection failures."""
        service = VideoEncoderService()
        
        from app.models.encoder.encoder_models import VideoEncoder
        
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100"
        )
        db_session.add(encoder)
        db_session.commit()
        
        mock_client = AsyncMock()
        mock_client.get_full_status.side_effect = ConnectionError("Connection refused")
        
        with patch.object(service, '_get_encoder_client', return_value=mock_client):
            with pytest.raises(EncoderConnectionError) as exc_info:
                await service.get_encoder_status(db_session, encoder.id)
            
            assert "Failed to get encoder status" in str(exc_info.value)


@pytest.mark.unit
class TestRecordingServiceErrorPaths:
    """Test CameraRecordingService error handling."""
    
    @pytest.mark.asyncio
    async def test_record_camera_missing_stream(self, db_session):
        """Test recording when camera stream is unavailable."""
        from services.camera.recording_service import CameraRecordingService
        
        service = CameraRecordingService()
        
        # Mock camera service to return no stream URL
        service.arlo_service.get_camera = AsyncMock(return_value={'id': 1})
        service.arlo_service.start_live_stream = AsyncMock(return_value={})  # No stream_url
        
        with pytest.raises(ArloCameraError) as exc_info:
            await service.record_camera(db_session, camera_id=1, encoder_id=1)
        
        assert "Could not get stream URL" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_record_camera_encoder_busy(self, db_session):
        """Test recording when encoder is already busy."""
        from services.camera.recording_service import CameraRecordingService
        
        service = CameraRecordingService()
        
        service.arlo_service.get_camera = AsyncMock(return_value={'id': 1})
        service.arlo_service.start_live_stream = AsyncMock(
            return_value={'stream_url': 'rtmp://example.com/stream'}
        )
        service.encoder_service.record_stream = AsyncMock(
            side_effect=EncoderRecordingError("Encoder already recording", encoder_id="1")
        )
        
        with pytest.raises(EncoderRecordingError):
            await service.record_camera(db_session, camera_id=1, encoder_id=1)


@pytest.mark.unit
class TestInvalidInputHandling:
    """Test handling of invalid input values."""
    
    @pytest.mark.asyncio
    async def test_camera_id_zero(self, db_session):
        """Test handling of camera ID = 0."""
        service = ArloService()
        
        with pytest.raises(ArloCameraError):
            await service.get_camera(db_session, 0)
    
    @pytest.mark.asyncio
    async def test_encoder_id_negative(self, db_session):
        """Test handling of negative encoder ID."""
        service = VideoEncoderService()
        
        with pytest.raises(EncoderError):
            await service.get_encoder(db_session, -1)
    
    @pytest.mark.asyncio
    async def test_record_duration_negative(self, db_session):
        """Test handling of negative duration."""
        service = VideoEncoderService()
        
        from app.models.encoder.encoder_models import VideoEncoder
        
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            is_recording=False
        )
        db_session.add(encoder)
        db_session.commit()
        
        # Service should handle negative duration (may use as None or validate)
        # This tests that it doesn't crash
        mock_client = AsyncMock()
        mock_client.configure_recording = AsyncMock()
        mock_client.start_recording = AsyncMock()
        
        with patch.object(service, '_get_encoder_client', return_value=mock_client):
            # Should not raise exception for negative duration (may be handled by client)
            try:
                await service.record_stream(
                    db_session,
                    encoder.id,
                    source_url="rtmp://example.com/stream",
                    duration=-1
                )
            except (EncoderError, EncoderRecordingError):
                # Acceptable if it validates and rejects
                pass

