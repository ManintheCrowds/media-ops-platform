"""Unit tests for camera recording service bridge logic."""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from services.camera.recording_service import CameraRecordingService
from app.exceptions import ArloCameraError, EncoderError


@pytest.fixture
def recording_service():
    """Create CameraRecordingService instance."""
    return CameraRecordingService()


@pytest.mark.unit
class TestCameraRecordingServiceInit:
    """Test CameraRecordingService initialization."""
    
    def test_init(self, recording_service):
        """Test service initialization."""
        assert recording_service.arlo_service is not None
        assert recording_service.encoder_service is not None
        assert recording_service.media_client is None


@pytest.mark.unit
class TestCameraRecordingServiceRecord:
    """Test camera recording via encoder."""
    
    @pytest.mark.asyncio
    async def test_record_camera_success(self, recording_service, db_session):
        """Test successfully recording camera via encoder."""
        # Mock camera service
        mock_camera = {'id': 1, 'name': 'Test Camera', 'device_id': 'CAM001'}
        mock_stream = {'stream_url': 'rtmp://camera.example.com/stream'}
        
        recording_service.arlo_service.get_camera = AsyncMock(return_value=mock_camera)
        recording_service.arlo_service.start_live_stream = AsyncMock(return_value=mock_stream)
        
        # Mock encoder service
        mock_recording = {
            'status': 'recording',
            'encoder_id': 1,
            'output_path': '/path/to/recording.mp4',
            'source_url': 'rtmp://camera.example.com/stream'
        }
        recording_service.encoder_service.record_stream = AsyncMock(return_value=mock_recording)
        
        result = await recording_service.record_camera(
            db_session,
            camera_id=1,
            encoder_id=1,
            duration=3600
        )
        
        assert result['status'] == 'recording'
        assert result['encoder_id'] == 1
        recording_service.arlo_service.get_camera.assert_called_once_with(db_session, 1)
        recording_service.arlo_service.start_live_stream.assert_called_once_with(db_session, 1)
        recording_service.encoder_service.record_stream.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_record_camera_no_stream_url(self, recording_service, db_session):
        """Test recording fails when stream URL is not available."""
        mock_camera = {'id': 1, 'name': 'Test Camera'}
        mock_stream = {}  # No stream_url
        
        recording_service.arlo_service.get_camera = AsyncMock(return_value=mock_camera)
        recording_service.arlo_service.start_live_stream = AsyncMock(return_value=mock_stream)
        
        with pytest.raises(ArloCameraError) as exc_info:
            await recording_service.record_camera(
                db_session,
                camera_id=1,
                encoder_id=1
            )
        
        assert "Could not get stream URL" in str(exc_info.value)
        assert exc_info.value.camera_id == "1"
    
    @pytest.mark.asyncio
    async def test_record_camera_camera_error(self, recording_service, db_session):
        """Test recording handles camera service errors."""
        recording_service.arlo_service.get_camera = AsyncMock(
            side_effect=ArloCameraError("Camera not found", camera_id="1")
        )
        
        with pytest.raises(ArloCameraError):
            await recording_service.record_camera(
                db_session,
                camera_id=1,
                encoder_id=1
            )
    
    @pytest.mark.asyncio
    async def test_record_camera_encoder_error(self, recording_service, db_session):
        """Test recording handles encoder service errors."""
        mock_camera = {'id': 1, 'name': 'Test Camera'}
        mock_stream = {'stream_url': 'rtmp://camera.example.com/stream'}
        
        recording_service.arlo_service.get_camera = AsyncMock(return_value=mock_camera)
        recording_service.arlo_service.start_live_stream = AsyncMock(return_value=mock_stream)
        recording_service.encoder_service.record_stream = AsyncMock(
            side_effect=EncoderError("Encoder not found", encoder_id="1")
        )
        
        with pytest.raises(EncoderError):
            await recording_service.record_camera(
                db_session,
                camera_id=1,
                encoder_id=1
            )
    
    @pytest.mark.asyncio
    async def test_record_camera_with_media_client(self, recording_service, db_session):
        """Test recording with media client configured."""
        mock_media_client = MagicMock()
        recording_service.media_client = mock_media_client
        
        mock_camera = {'id': 1, 'name': 'Test Camera'}
        mock_stream = {'stream_url': 'rtmp://camera.example.com/stream'}
        mock_recording = {
            'status': 'recording',
            'encoder_id': 1,
            'output_path': '/path/to/recording.mp4'
        }
        
        recording_service.arlo_service.get_camera = AsyncMock(return_value=mock_camera)
        recording_service.arlo_service.start_live_stream = AsyncMock(return_value=mock_stream)
        recording_service.encoder_service.record_stream = AsyncMock(return_value=mock_recording)
        
        result = await recording_service.record_camera(
            db_session,
            camera_id=1,
            encoder_id=1
        )
        
        assert result['status'] == 'recording'
        # Media client upload would be logged but not executed during recording


@pytest.mark.unit
class TestCameraRecordingServiceStop:
    """Test stopping recording."""
    
    @pytest.mark.asyncio
    async def test_stop_recording_success(self, recording_service, db_session):
        """Test successfully stopping recording."""
        mock_result = {
            'status': 'stopped',
            'encoder_id': 1,
            'recording_path': '/path/to/recording.mp4'
        }
        
        recording_service.encoder_service.stop_recording = AsyncMock(return_value=mock_result)
        
        result = await recording_service.stop_recording(db_session, encoder_id=1)
        
        assert result['status'] == 'stopped'
        assert result['encoder_id'] == 1
        recording_service.encoder_service.stop_recording.assert_called_once_with(db_session, 1)
    
    @pytest.mark.asyncio
    async def test_stop_recording_encoder_error(self, recording_service, db_session):
        """Test stopping handles encoder errors."""
        recording_service.encoder_service.stop_recording = AsyncMock(
            side_effect=EncoderError("Encoder not found", encoder_id="1")
        )
        
        with pytest.raises(EncoderError):
            await recording_service.stop_recording(db_session, encoder_id=1)


@pytest.mark.unit
class TestCameraRecordingServiceErrorPropagation:
    """Test error propagation through bridge service."""
    
    @pytest.mark.asyncio
    async def test_error_propagates_from_camera(self, recording_service, db_session):
        """Test that camera errors propagate correctly."""
        recording_service.arlo_service.get_camera = AsyncMock(
            side_effect=ArloCameraError("Camera error", camera_id="1")
        )
        
        with pytest.raises(ArloCameraError) as exc_info:
            await recording_service.record_camera(db_session, camera_id=1, encoder_id=1)
        
        assert exc_info.value.camera_id == "1"
    
    @pytest.mark.asyncio
    async def test_error_propagates_from_encoder(self, recording_service, db_session):
        """Test that encoder errors propagate correctly."""
        mock_camera = {'id': 1, 'name': 'Test Camera'}
        mock_stream = {'stream_url': 'rtmp://camera.example.com/stream'}
        
        recording_service.arlo_service.get_camera = AsyncMock(return_value=mock_camera)
        recording_service.arlo_service.start_live_stream = AsyncMock(return_value=mock_stream)
        recording_service.encoder_service.record_stream = AsyncMock(
            side_effect=EncoderError("Encoder error", encoder_id="1")
        )
        
        with pytest.raises(EncoderError) as exc_info:
            await recording_service.record_camera(db_session, camera_id=1, encoder_id=1)
        
        assert exc_info.value.encoder_id == "1"

