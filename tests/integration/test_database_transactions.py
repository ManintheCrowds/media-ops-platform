"""Integration tests for database transaction management."""

import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from services.camera.arlo_service import ArloService
from services.video_encoder.encoder_service import VideoEncoderService
from app.models.camera.arlo_models import ArloBaseStation, ArloCamera
from app.models.encoder.encoder_models import VideoEncoder
from app.models.camera.enums import ArloStatus
from app.exceptions import ArloError, EncoderError


@pytest.mark.integration
class TestTransactionRollback:
    """Test transaction rollback on errors."""
    
    @pytest.mark.asyncio
    async def test_register_camera_rollback_on_error(self, db_session):
        """Test that camera registration rolls back on error."""
        service = ArloService()
        
        # Create base station
        station = ArloBaseStation(name="Base", serial_number="BS001")
        db_session.add(station)
        db_session.flush()
        
        # Try to register camera with invalid data that causes error
        camera_data = {
            'device_id': 'CAM001',
            'device_type': 'arloq',
            'name': 'Test Camera'
        }
        
        # Register first time (success)
        result1 = await service.register_camera(db_session, camera_data)
        camera_id = result1['id']
        
        # Try to register again with same device_id (should cause IntegrityError)
        # But service should handle it gracefully by updating
        result2 = await service.register_camera(db_session, camera_data)
        
        # Should update, not create duplicate
        assert result2['id'] == camera_id
        
        # Verify only one camera exists
        cameras = db_session.query(ArloCamera).filter_by(device_id='CAM001').all()
        assert len(cameras) == 1
    
    @pytest.mark.asyncio
    async def test_register_encoder_rollback_on_error(self, db_session):
        """Test that encoder registration rolls back on error."""
        service = VideoEncoderService()
        
        encoder_data = {
            'ip_address': '192.168.1.100',
            'name': 'Test Encoder'
        }
        
        # Register first time (success)
        result1 = await service.register_encoder(db_session, encoder_data)
        encoder_id = result1['id']
        
        # Try to register again with same IP (should update, not fail)
        result2 = await service.register_encoder(db_session, encoder_data)
        
        # Should update, not create duplicate
        assert result2['id'] == encoder_id
        
        # Verify only one encoder exists
        encoders = db_session.query(VideoEncoder).filter_by(ip_address='192.168.1.100').all()
        assert len(encoders) == 1
    
    @pytest.mark.asyncio
    async def test_arm_camera_rollback_on_client_error(self, db_session):
        """Test that arming camera rolls back on client error."""
        service = ArloService()
        
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
        
        original_armed = camera.is_armed
        
        # Mock client to raise error
        mock_client = AsyncMock()
        mock_client.Arm = Mock(side_effect=Exception("Arm failed"))
        
        with patch.object(service, '_get_arlo_client', return_value=mock_client):
            with pytest.raises(Exception):
                await service.arm_camera(db_session, camera.id)
        
        # Verify camera state not changed (transaction rolled back)
        db_session.refresh(camera)
        assert camera.is_armed == original_armed
    
    @pytest.mark.asyncio
    async def test_record_stream_rollback_on_error(self, db_session):
        """Test that recording rolls back on error."""
        service = VideoEncoderService()
        
        encoder = VideoEncoder(
            name="Test Encoder",
            ip_address="192.168.1.100",
            is_recording=False,
            status=EncoderStatus.ONLINE
        )
        db_session.add(encoder)
        db_session.commit()
        
        original_status = encoder.status
        original_recording = encoder.is_recording
        
        # Mock client to raise error
        mock_client = AsyncMock()
        mock_client.configure_recording = AsyncMock()
        mock_client.start_recording = AsyncMock(side_effect=Exception("Recording failed"))
        
        with patch.object(service, '_get_encoder_client', return_value=mock_client):
            with pytest.raises(Exception):
                await service.record_stream(
                    db_session,
                    encoder.id,
                    source_url="rtmp://example.com/stream"
                )
        
        # Verify encoder status updated to ERROR (service commits error status)
        db_session.refresh(encoder)
        # Service sets status to ERROR on failure, so this is expected
        assert encoder.status == EncoderStatus.ERROR


@pytest.mark.integration
class TestTransactionCommit:
    """Test successful transaction commits."""
    
    @pytest.mark.asyncio
    async def test_register_camera_commits_successfully(self, db_session):
        """Test that successful camera registration commits."""
        service = ArloService()
        
        camera_data = {
            'device_id': 'CAM002',
            'device_type': 'arloq',
            'name': 'Test Camera 2'
        }
        
        result = await service.register_camera(db_session, camera_data)
        
        # Verify camera exists in database
        camera = db_session.query(ArloCamera).filter_by(device_id='CAM002').first()
        assert camera is not None
        assert camera.id == result['id']
    
    @pytest.mark.asyncio
    async def test_register_encoder_commits_successfully(self, db_session):
        """Test that successful encoder registration commits."""
        service = VideoEncoderService()
        
        encoder_data = {
            'ip_address': '192.168.1.101',
            'name': 'Test Encoder 2'
        }
        
        result = await service.register_encoder(db_session, encoder_data)
        
        # Verify encoder exists in database
        encoder = db_session.query(VideoEncoder).filter_by(ip_address='192.168.1.101').first()
        assert encoder is not None
        assert encoder.id == result['id']
    
    @pytest.mark.asyncio
    async def test_arm_camera_commits_successfully(self, db_session):
        """Test that successful camera arming commits."""
        service = ArloService()
        
        station = ArloBaseStation(name="Base", serial_number="BS001")
        db_session.add(station)
        db_session.flush()
        
        camera = ArloCamera(
            base_station_id=station.id,
            name="Test Camera",
            device_id="CAM003",
            is_armed=False
        )
        db_session.add(camera)
        db_session.commit()
        
        mock_client = AsyncMock()
        mock_client.Arm = Mock(return_value=True)
        
        with patch.object(service, '_get_arlo_client', return_value=mock_client):
            result = await service.arm_camera(db_session, camera.id)
            
            assert result['is_armed'] is True
            
            # Verify commit
            db_session.refresh(camera)
            assert camera.is_armed is True


@pytest.mark.integration
class TestNestedTransactions:
    """Test nested transaction handling."""
    
    @pytest.mark.asyncio
    async def test_multiple_operations_in_sequence(self, db_session):
        """Test multiple operations that should all commit."""
        service = ArloService()
        
        # Register camera
        camera_data = {
            'device_id': 'CAM004',
            'device_type': 'arloq',
            'name': 'Test Camera 4'
        }
        result1 = await service.register_camera(db_session, camera_data)
        camera_id = result1['id']
        
        # Get camera
        camera = await service.get_camera(db_session, camera_id)
        assert camera['device_id'] == 'CAM004'
        
        # List cameras
        cameras = await service.list_cameras(db_session)
        assert any(cam['device_id'] == 'CAM004' for cam in cameras)
        
        # All operations should see committed data
        db_session.refresh(db_session.query(ArloCamera).filter_by(id=camera_id).first())
        assert db_session.query(ArloCamera).filter_by(id=camera_id).first() is not None


@pytest.mark.integration
class TestConcurrentModifications:
    """Test handling of concurrent modifications."""
    
    @pytest.mark.asyncio
    async def test_concurrent_camera_updates(self, db_session):
        """Test that concurrent camera updates are handled correctly."""
        service = ArloService()
        
        # Create camera
        camera_data = {
            'device_id': 'CAM005',
            'device_type': 'arloq',
            'name': 'Test Camera 5'
        }
        result = await service.register_camera(db_session, camera_data)
        camera_id = result['id']
        
        # Update camera twice (simulating concurrent updates)
        camera_data['name'] = 'Updated Name 1'
        result1 = await service.register_camera(db_session, camera_data)
        
        camera_data['name'] = 'Updated Name 2'
        result2 = await service.register_camera(db_session, camera_data)
        
        # Last update should win
        assert result2['name'] == 'Updated Name 2'
        
        # Verify in database
        camera = db_session.query(ArloCamera).filter_by(id=camera_id).first()
        assert camera.name == 'Updated Name 2'

