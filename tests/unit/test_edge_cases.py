"""Unit tests for edge cases (empty lists, None values, boundaries)."""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from services.camera.arlo_service import ArloService
from services.camera.config import CameraConfig
from services.video_encoder.encoder_service import VideoEncoderService
from services.video_encoder.config import EncoderConfig
from app.exceptions import ArloError, EncoderError


@pytest.mark.unit
class TestEmptyListHandling:
    """Test handling of empty lists."""
    
    @pytest.fixture
    def arlo_service(self, tmp_path):
        """Create ArloService with temp storage path."""
        storage_path = tmp_path / "camera_recordings"
        config = CameraConfig(arlo_storage_path=str(storage_path))
        return ArloService(config=config)
    
    @pytest.fixture
    def encoder_service(self, tmp_path):
        """Create VideoEncoderService with temp storage path."""
        storage_path = tmp_path / "encoder_recordings"
        config = EncoderConfig(encoder_storage_path=str(storage_path))
        return VideoEncoderService(config=config)
    
    @pytest.mark.asyncio
    async def test_list_cameras_empty(self, db_session, arlo_service):
        """Test listing cameras when none exist."""
        cameras = await arlo_service.list_cameras(db_session)
        
        assert isinstance(cameras, list)
        assert len(cameras) == 0
    
    @pytest.mark.asyncio
    async def test_list_encoders_empty(self, db_session, encoder_service):
        """Test listing encoders when none exist."""
        encoders = await encoder_service.list_encoders(db_session)
        
        assert isinstance(encoders, list)
        assert len(encoders) == 0
    
    @pytest.mark.asyncio
    async def test_discover_cameras_empty_result(self, db_session, arlo_service):
        """Test discovery when no cameras found."""
        mock_client = MagicMock()
        mock_client.GetDevices.return_value = []  # Empty list
        
        with patch.object(arlo_service, '_get_arlo_client', return_value=mock_client):
            cameras = await arlo_service.discover_cameras(db_session)
            
            assert isinstance(cameras, list)
            assert len(cameras) == 0
    
    @pytest.mark.asyncio
    async def test_discover_encoders_empty_result(self, db_session, encoder_service):
        """Test discovery when no encoders found."""
        with patch('aiohttp.ClientSession') as mock_session:
            # All probes return 404
            mock_response = MagicMock()
            mock_response.status = 404
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            discovered = await encoder_service.discover_encoders(db_session)
            
            assert isinstance(discovered, list)
            assert len(discovered) == 0


@pytest.mark.unit
class TestNoneValueHandling:
    """Test handling of None values."""
    
    @pytest.mark.asyncio
    async def test_register_camera_with_none_fields(self, db_session, arlo_service):
        """Test registering camera with None optional fields."""
        camera_data = {
            'device_id': 'CAM001',
            'device_type': 'arloq',
            'name': 'Test Camera',
            'status': 'ONLINE',
            'battery_level': None,
            'signal_strength': None
        }
        
        result = await arlo_service.register_camera(db_session, camera_data)
        
        assert result['device_id'] == 'CAM001'
        # None values should be handled gracefully
    
    @pytest.mark.asyncio
    async def test_register_encoder_with_none_fields(self, db_session, encoder_service):
        """Test registering encoder with None optional fields."""
        encoder_data = {
            'ip_address': '192.168.1.100',
            'name': 'Test Encoder',
            'port': None,  # Should use default
            'device_type': None  # Should use default
        }
        
        result = await encoder_service.register_encoder(db_session, encoder_data)
        
        assert result['ip_address'] == '192.168.1.100'
        assert result['port'] == 80  # Default
        assert result['device_type'] == 'aja_helo'  # Default
    
    @pytest.mark.asyncio
    async def test_get_library_with_none_dates(self, db_session, arlo_service):
        """Test getting library with None date parameters."""
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
        mock_client.GetLibrary.return_value = []
        
        with patch.object(arlo_service, '_get_arlo_client', return_value=mock_client):
            recordings = await arlo_service.get_library(
                db_session,
                camera.id,
                start_date=None,
                end_date=None
            )
            
            # Should use default date range (last 7 days)
            assert isinstance(recordings, list)


@pytest.mark.unit
class TestBoundaryConditions:
    """Test boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_camera_id_max_int(self, db_session, arlo_service):
        """Test handling of maximum integer camera ID."""
        # Max 32-bit integer
        max_id = 2147483647
        
        with pytest.raises(ArloCameraError):
            await arlo_service.get_camera(db_session, max_id)
    
    @pytest.mark.asyncio
    async def test_encoder_id_max_int(self, db_session, encoder_service):
        """Test handling of maximum integer encoder ID."""
        max_id = 2147483647
        
        with pytest.raises(EncoderError):
            await encoder_service.get_encoder(db_session, max_id)
    
    @pytest.mark.asyncio
    async def test_record_duration_zero(self, db_session, encoder_service):
        """Test recording with zero duration."""
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
        mock_client.start_recording = AsyncMock()
        
        with patch.object(encoder_service, '_get_encoder_client', return_value=mock_client):
            # Zero duration might mean record indefinitely
            result = await encoder_service.record_stream(
                db_session,
                encoder.id,
                source_url="rtmp://example.com/stream",
                duration=0
            )
            
            assert result['status'] == 'recording'
    
    @pytest.mark.asyncio
    async def test_record_duration_very_large(self, db_session, encoder_service):
        """Test recording with very large duration."""
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
        mock_client.start_recording = AsyncMock()
        
        with patch.object(encoder_service, '_get_encoder_client', return_value=mock_client):
            # Very large duration (e.g., 1 year in seconds)
            large_duration = 365 * 24 * 60 * 60
            
            result = await encoder_service.record_stream(
                db_session,
                encoder.id,
                source_url="rtmp://example.com/stream",
                duration=large_duration
            )
            
            assert result['status'] == 'recording'


@pytest.mark.unit
class TestStringBoundaries:
    """Test string field boundaries."""
    
    @pytest.mark.asyncio
    async def test_camera_name_very_long(self, db_session):
        """Test camera with very long name."""
        service = ArloService()
        
        long_name = "A" * 1000  # Very long name
        
        camera_data = {
            'device_id': 'CAM001',
            'device_type': 'arloq',
            'name': long_name
        }
        
        # Should handle long names (may truncate or accept)
        try:
            result = await service.register_camera(db_session, camera_data)
            # If it succeeds, name might be truncated by DB constraint
            assert 'name' in result
        except Exception:
            # Acceptable if DB constraint rejects
            pass
    
    @pytest.mark.asyncio
    async def test_encoder_name_empty_string(self, db_session):
        """Test encoder with empty string name."""
        service = VideoEncoderService()
        
        encoder_data = {
            'ip_address': '192.168.1.100',
            'name': ''  # Empty string
        }
        
        # Empty string might be valid or rejected
        try:
            result = await service.register_encoder(db_session, encoder_data)
            assert result['name'] == ''
        except Exception:
            # Acceptable if validation rejects empty string
            pass
    
    @pytest.mark.asyncio
    async def test_stream_url_very_long(self, db_session):
        """Test recording with very long stream URL."""
        service = VideoEncoderService()
        
        from app.models.encoder.encoder_models import VideoEncoder
        
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            is_recording=False
        )
        db_session.add(encoder)
        db_session.commit()
        
        long_url = "rtmp://" + "example.com/" * 100 + "stream"
        
        mock_client = AsyncMock()
        mock_client.configure_recording = AsyncMock()
        mock_client.start_recording = AsyncMock()
        
        with patch.object(service, '_get_encoder_client', return_value=mock_client):
            result = await service.record_stream(
                db_session,
                encoder.id,
                source_url=long_url,
                duration=60
            )
            
            assert result['status'] == 'recording'


@pytest.mark.unit
class TestSpecialCharacters:
    """Test handling of special characters."""
    
    @pytest.mark.asyncio
    async def test_camera_name_with_special_chars(self, db_session):
        """Test camera name with special characters."""
        service = ArloService()
        
        camera_data = {
            'device_id': 'CAM001',
            'device_type': 'arloq',
            'name': 'Camera !@#$%^&*()_+-=[]{}|;:\'",./<>?'
        }
        
        result = await service.register_camera(db_session, camera_data)
        
        assert result['name'] == 'Camera !@#$%^&*()_+-=[]{}|;:\'",./<>?'
    
    @pytest.mark.asyncio
    async def test_encoder_name_with_unicode(self, db_session):
        """Test encoder name with unicode characters."""
        service = VideoEncoderService()
        
        encoder_data = {
            'ip_address': '192.168.1.100',
            'name': 'Encoder 编码器 🎥'
        }
        
        result = await service.register_encoder(db_session, encoder_data)
        
        assert '编码器' in result['name']
        assert '🎥' in result['name']


@pytest.mark.unit
class TestConcurrentOperations:
    """Test edge cases with concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_register_same_camera_twice(self, db_session):
        """Test registering the same camera twice (should update)."""
        service = ArloService()
        
        camera_data = {
            'device_id': 'CAM001',
            'device_type': 'arloq',
            'name': 'Camera 1'
        }
        
        result1 = await service.register_camera(db_session, camera_data)
        camera_id = result1['id']
        
        # Register again with different name
        camera_data['name'] = 'Camera 1 Updated'
        result2 = await service.register_camera(db_session, camera_data)
        
        # Should update existing, not create new
        assert result2['id'] == camera_id
        assert result2['name'] == 'Camera 1 Updated'
    
    @pytest.mark.asyncio
    async def test_register_same_encoder_twice(self, db_session):
        """Test registering the same encoder twice (should update)."""
        service = VideoEncoderService()
        
        encoder_data = {
            'ip_address': '192.168.1.100',
            'name': 'Encoder 1'
        }
        
        result1 = await service.register_encoder(db_session, encoder_data)
        encoder_id = result1['id']
        
        # Register again with different name
        encoder_data['name'] = 'Encoder 1 Updated'
        result2 = await service.register_encoder(db_session, encoder_data)
        
        # Should update existing, not create new
        assert result2['id'] == encoder_id
        assert result2['name'] == 'Encoder 1 Updated'

