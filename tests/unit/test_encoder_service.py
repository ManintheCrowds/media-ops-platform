"""Unit tests for video encoder service with mocked dependencies."""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime
from pathlib import Path

from services.video_encoder.encoder_service import VideoEncoderService
from services.video_encoder.config import EncoderConfig
from app.models.encoder.encoder_models import VideoEncoder
from app.models.encoder.enums import EncoderStatus, EncoderDeviceType
from app.exceptions import (
    EncoderError,
    EncoderConnectionError,
    EncoderRecordingError
)


@pytest.fixture
def mock_aja_client():
    """Create a mock AJA HELO client."""
    mock = AsyncMock()
    mock.configure_recording = AsyncMock()
    mock.start_recording = AsyncMock()
    mock.stop_recording = AsyncMock()
    mock.get_full_status = AsyncMock(return_value={
        'recording': False,
        'streaming': False,
        'status': 'online'
    })
    return mock


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock encoder config."""
    storage_path = tmp_path / "recordings"
    config = EncoderConfig(
        storage_path=str(storage_path),
        encoder_network_scan_range="192.168.1.0/24"
    )
    return config


@pytest.fixture
def encoder_service(mock_config):
    """Create VideoEncoderService instance with mocked config."""
    service = VideoEncoderService(config=mock_config)
    return service


@pytest.mark.unit
class TestVideoEncoderServiceInit:
    """Test VideoEncoderService initialization."""
    
    def test_init_with_config(self, mock_config):
        """Test service initialization with config."""
        service = VideoEncoderService(config=mock_config)
        
        assert service.config == mock_config
        assert service.storage_path.exists()
    
    def test_init_with_default_config(self):
        """Test service initialization with default config."""
        service = VideoEncoderService()
        
        assert service.config is not None
        assert isinstance(service.config, EncoderConfig)


@pytest.mark.unit
class TestVideoEncoderServiceGetClient:
    """Test VideoEncoderService client management."""
    
    def test_get_client_success(self, encoder_service, db_session, mock_aja_client):
        """Test getting encoder client successfully."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            port=80
        )
        db_session.add(encoder)
        db_session.commit()
        
        with patch('services.video_encoder.encoder_service.AJAHELOClient', return_value=mock_aja_client):
            client = encoder_service._get_encoder_client(encoder)
            
            assert client == mock_aja_client
    
    def test_get_client_caches_instance(self, encoder_service, db_session, mock_aja_client):
        """Test that client instances are cached."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            port=80
        )
        db_session.add(encoder)
        db_session.commit()
        
        with patch('services.video_encoder.encoder_service.AJAHELOClient', return_value=mock_aja_client):
            client1 = encoder_service._get_encoder_client(encoder)
            client2 = encoder_service._get_encoder_client(encoder)
            
            assert client1 == client2
            assert len(encoder_service._clients) == 1
    
    def test_get_client_connection_error(self, encoder_service, db_session):
        """Test error when client initialization fails."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            port=80
        )
        db_session.add(encoder)
        db_session.commit()
        
        with patch('services.video_encoder.encoder_service.AJAHELOClient', side_effect=Exception("Connection failed")):
            with pytest.raises(EncoderConnectionError) as exc_info:
                encoder_service._get_encoder_client(encoder)
            
            assert "Failed to initialize encoder client" in str(exc_info.value)


@pytest.mark.unit
class TestVideoEncoderServiceDiscover:
    """Test encoder discovery."""
    
    @pytest.mark.asyncio
    async def test_discover_encoders_success(self, encoder_service, db_session):
        """Test successful encoder discovery."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'device_name': 'AJA HELO',
            'firmware_version': '1.0.0'
        })
        mock_get_ctx = AsyncMock()
        mock_get_ctx.__aenter__.return_value = mock_response
        mock_get_ctx.__aexit__.return_value = None
        session_instance = MagicMock()
        session_instance.get.return_value = mock_get_ctx
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = session_instance
        mock_session_ctx.__aexit__.return_value = None

        with patch('aiohttp.ClientSession', return_value=mock_session_ctx):
            discovered = await encoder_service.discover_encoders(db_session, "192.168.1.100/32")

            assert len(discovered) == 1
            assert discovered[0]['ip_address'] == '192.168.1.100'
            assert all('device_type' in enc for enc in discovered)
    
    @pytest.mark.asyncio
    async def test_discover_encoders_no_results(self, encoder_service, db_session):
        """Test discovery with no encoders found."""
        mock_response = MagicMock()
        mock_response.status = 404
        
        with patch('aiohttp.ClientSession', new_callable=AsyncMock) as mock_session:
            session_instance = AsyncMock()
            session_instance.get.return_value.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value = session_instance
            
            discovered = await encoder_service.discover_encoders(db_session, "192.168.1.0/24")
            
            assert len(discovered) == 0
    
    @pytest.mark.asyncio
    async def test_discover_encoders_uses_default_range(self, encoder_service, db_session):
        """Test discovery uses default network range when not provided."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'device_name': 'AJA HELO'})
        
        with patch('aiohttp.ClientSession', new_callable=AsyncMock) as mock_session:
            session_instance = AsyncMock()
            session_instance.get.return_value.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value = session_instance
            
            discovered = await encoder_service.discover_encoders(db_session)
            
            # Should use default range from config
            assert isinstance(discovered, list)


@pytest.mark.unit
class TestVideoEncoderServiceRegister:
    """Test encoder registration."""
    
    @pytest.mark.asyncio
    async def test_register_encoder_new(self, encoder_service, db_session):
        """Test registering a new encoder."""
        encoder_data = {
            'ip_address': '192.168.1.100',
            'name': 'Test Encoder',
            'port': 80,
            'device_type': 'AJA_HELO'
        }
        
        result = await encoder_service.register_encoder(db_session, encoder_data)
        
        assert result['ip_address'] == '192.168.1.100'
        assert result['name'] == 'Test Encoder'
        
        # Verify in database
        encoder = db_session.query(VideoEncoder).filter_by(ip_address='192.168.1.100').first()
        assert encoder is not None
        assert encoder.name == 'Test Encoder'
    
    @pytest.mark.asyncio
    async def test_register_encoder_existing(self, encoder_service, db_session):
        """Test updating an existing encoder."""
        # Create existing encoder
        encoder = VideoEncoder(
            name="Old Name",
            ip_address="192.168.1.100",
            status=EncoderStatus.OFFLINE
        )
        db_session.add(encoder)
        db_session.commit()
        
        # Update encoder
        encoder_data = {
            'ip_address': '192.168.1.100',
            'name': 'New Name',
            'device_type': 'AJA_HELO'
        }
        
        result = await encoder_service.register_encoder(db_session, encoder_data)
        
        assert result['name'] == 'New Name'
        
        # Verify update
        db_session.refresh(encoder)
        assert encoder.name == 'New Name'
    
    @pytest.mark.asyncio
    async def test_register_encoder_missing_fields(self, encoder_service, db_session):
        """Test registration fails with missing required fields."""
        encoder_data = {
            'ip_address': '192.168.1.100'
            # Missing name
        }
        
        with pytest.raises(EncoderError) as exc_info:
            await encoder_service.register_encoder(db_session, encoder_data)
        
        assert "Missing required field" in str(exc_info.value)


@pytest.mark.unit
class TestVideoEncoderServiceListGet:
    """Test listing and getting encoders."""
    
    @pytest.mark.asyncio
    async def test_list_encoders(self, encoder_service, db_session):
        """Test listing all encoders."""
        # Create test data
        encoder1 = VideoEncoder(name="Encoder 1", ip_address="192.168.1.100")
        encoder2 = VideoEncoder(name="Encoder 2", ip_address="192.168.1.101")
        db_session.add_all([encoder1, encoder2])
        db_session.commit()
        
        encoders = await encoder_service.list_encoders(db_session)
        
        assert len(encoders) == 2
        assert all('id' in enc for enc in encoders)
        assert all('name' in enc for enc in encoders)
    
    @pytest.mark.asyncio
    async def test_get_encoder_success(self, encoder_service, db_session):
        """Test getting encoder by ID."""
        encoder = VideoEncoder(name="Test Encoder", ip_address="192.168.1.100")
        db_session.add(encoder)
        db_session.commit()
        
        result = await encoder_service.get_encoder(db_session, encoder.id)
        
        assert result['id'] == encoder.id
        assert result['name'] == 'Test Encoder'
    
    @pytest.mark.asyncio
    async def test_get_encoder_not_found(self, encoder_service, db_session):
        """Test getting non-existent encoder raises error."""
        with pytest.raises(EncoderError) as exc_info:
            await encoder_service.get_encoder(db_session, 999)
        
        assert "Encoder not found" in str(exc_info.value)


@pytest.mark.unit
class TestVideoEncoderServiceRecord:
    """Test recording operations."""
    
    @pytest.mark.asyncio
    async def test_record_stream_success(self, encoder_service, db_session, mock_aja_client):
        """Test successfully starting recording."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            is_recording=False
        )
        db_session.add(encoder)
        db_session.commit()
        
        with patch.object(encoder_service, '_get_encoder_client', return_value=mock_aja_client):
            result = await encoder_service.record_stream(
                db_session,
                encoder.id,
                "rtmp://source.example.com/stream",
                duration=60
            )
            
            assert result['status'] == 'recording'
            assert result['encoder_id'] == encoder.id
            assert 'output_path' in result
            mock_aja_client.configure_recording.assert_called_once()
            mock_aja_client.start_recording.assert_called_once()
            
            # Verify encoder updated
            db_session.refresh(encoder)
            assert encoder.is_recording is True
            assert encoder.status == EncoderStatus.RECORDING
    
    @pytest.mark.asyncio
    async def test_record_stream_already_recording(self, encoder_service, db_session):
        """Test recording fails if encoder is already recording."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            is_recording=True
        )
        db_session.add(encoder)
        db_session.commit()
        
        with pytest.raises(EncoderRecordingError) as exc_info:
            await encoder_service.record_stream(
                db_session,
                encoder.id,
                "rtmp://source.example.com/stream"
            )
        
        assert "already recording" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_record_stream_not_found(self, encoder_service, db_session):
        """Test recording fails for non-existent encoder."""
        with pytest.raises(EncoderError):
            await encoder_service.record_stream(
                db_session,
                999,
                "rtmp://source.example.com/stream"
            )
    
    @pytest.mark.asyncio
    async def test_record_stream_client_error(self, encoder_service, db_session, mock_aja_client):
        """Test recording handles client errors."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            is_recording=False
        )
        db_session.add(encoder)
        db_session.commit()
        
        mock_aja_client.start_recording.side_effect = Exception("Recording failed")
        
        with patch.object(encoder_service, '_get_encoder_client', return_value=mock_aja_client):
            with pytest.raises(EncoderRecordingError) as exc_info:
                await encoder_service.record_stream(
                    db_session,
                    encoder.id,
                    "rtmp://source.example.com/stream"
                )
            
            assert "Failed to start recording" in str(exc_info.value)
            
            # Verify encoder status updated to ERROR
            db_session.refresh(encoder)
            assert encoder.status == EncoderStatus.ERROR


@pytest.mark.unit
class TestVideoEncoderServiceStop:
    """Test stopping recording."""
    
    @pytest.mark.asyncio
    async def test_stop_recording_success(self, encoder_service, db_session, mock_aja_client):
        """Test successfully stopping recording."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            is_recording=True,
            current_recording_path="/path/to/recording.mp4",
            status=EncoderStatus.RECORDING
        )
        db_session.add(encoder)
        db_session.commit()
        
        with patch.object(encoder_service, '_get_encoder_client', return_value=mock_aja_client):
            result = await encoder_service.stop_recording(db_session, encoder.id)
            
            assert result['status'] == 'stopped'
            assert result['encoder_id'] == encoder.id
            mock_aja_client.stop_recording.assert_called_once()
            
            # Verify encoder updated
            db_session.refresh(encoder)
            assert encoder.is_recording is False
            assert encoder.status == EncoderStatus.ONLINE
            assert encoder.current_recording_path is None
    
    @pytest.mark.asyncio
    async def test_stop_recording_not_recording(self, encoder_service, db_session):
        """Test stopping fails if encoder is not recording."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            is_recording=False
        )
        db_session.add(encoder)
        db_session.commit()
        
        with pytest.raises(EncoderRecordingError) as exc_info:
            await encoder_service.stop_recording(db_session, encoder.id)
        
        assert "not recording" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_stop_recording_not_found(self, encoder_service, db_session):
        """Test stopping fails for non-existent encoder."""
        with pytest.raises(EncoderError):
            await encoder_service.stop_recording(db_session, 999)


@pytest.mark.unit
class TestVideoEncoderServiceStatus:
    """Test encoder status checking."""
    
    @pytest.mark.asyncio
    async def test_get_encoder_status_success(self, encoder_service, db_session, mock_aja_client):
        """Test successfully getting encoder status."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100"
        )
        db_session.add(encoder)
        db_session.commit()
        
        mock_aja_client.get_full_status.return_value = {
            'recording': False,
            'streaming': False,
            'status': 'online'
        }
        
        with patch.object(encoder_service, '_get_encoder_client', return_value=mock_aja_client):
            result = await encoder_service.get_encoder_status(db_session, encoder.id)
            
            assert result['encoder_id'] == encoder.id
            assert result['status'] == 'online'
            assert 'device_status' in result
    
    @pytest.mark.asyncio
    async def test_get_encoder_status_recording(self, encoder_service, db_session, mock_aja_client):
        """Test status when encoder is recording."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100"
        )
        db_session.add(encoder)
        db_session.commit()
        
        mock_aja_client.get_full_status.return_value = {
            'recording': True,
            'streaming': False,
            'status': 'recording'
        }
        
        with patch.object(encoder_service, '_get_encoder_client', return_value=mock_aja_client):
            result = await encoder_service.get_encoder_status(db_session, encoder.id)
            
            assert result['status'] == 'recording'
            assert result['is_recording'] is True
            
            # Verify encoder updated
            db_session.refresh(encoder)
            assert encoder.is_recording is True
            assert encoder.status == EncoderStatus.RECORDING
    
    @pytest.mark.asyncio
    async def test_get_encoder_status_not_found(self, encoder_service, db_session):
        """Test status check fails for non-existent encoder."""
        with pytest.raises(EncoderError):
            await encoder_service.get_encoder_status(db_session, 999)
    
    @pytest.mark.asyncio
    async def test_get_encoder_status_connection_error(self, encoder_service, db_session, mock_aja_client):
        """Test status check handles connection errors."""
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100"
        )
        db_session.add(encoder)
        db_session.commit()
        
        mock_aja_client.get_full_status.side_effect = Exception("Connection failed")
        
        with patch.object(encoder_service, '_get_encoder_client', return_value=mock_aja_client):
            with pytest.raises(EncoderConnectionError) as exc_info:
                await encoder_service.get_encoder_status(db_session, encoder.id)
            
            assert "Failed to get encoder status" in str(exc_info.value)
            
            # Verify encoder status updated to ERROR
            db_session.refresh(encoder)
            assert encoder.status == EncoderStatus.ERROR

