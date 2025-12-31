"""Unit tests for custom exception classes."""

import pytest

from app.exceptions import (
    ArloError,
    ArloConnectionError,
    ArloCameraError,
    ArloRecordingError,
    EncoderError,
    EncoderConnectionError,
    EncoderRecordingError
)


@pytest.mark.unit
class TestArloExceptions:
    """Test Arlo exception classes."""
    
    def test_arlo_error_basic(self):
        """Test basic ArloError creation."""
        error = ArloError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.camera_id is None
        assert error.error_type is None
        assert isinstance(error, Exception)
    
    def test_arlo_error_with_camera_id(self):
        """Test ArloError with camera ID."""
        error = ArloError("Camera not found", camera_id="CAM123")
        
        assert error.message == "Camera not found"
        assert error.camera_id == "CAM123"
        assert error.error_type is None
    
    def test_arlo_error_with_all_params(self):
        """Test ArloError with all parameters."""
        error = ArloError(
            "Operation failed",
            camera_id="CAM456",
            error_type="connection_timeout"
        )
        
        assert error.message == "Operation failed"
        assert error.camera_id == "CAM456"
        assert error.error_type == "connection_timeout"
    
    def test_arlo_connection_error(self):
        """Test ArloConnectionError."""
        error = ArloConnectionError("Connection failed", camera_id="CAM789")
        
        assert isinstance(error, ArloError)
        assert isinstance(error, Exception)
        assert error.message == "Connection failed"
        assert error.camera_id == "CAM789"
    
    def test_arlo_camera_error(self):
        """Test ArloCameraError."""
        error = ArloCameraError("Camera operation failed")
        
        assert isinstance(error, ArloError)
        assert isinstance(error, Exception)
        assert error.message == "Camera operation failed"
    
    def test_arlo_recording_error(self):
        """Test ArloRecordingError."""
        error = ArloRecordingError("Recording failed", camera_id="CAM999")
        
        assert isinstance(error, ArloError)
        assert isinstance(error, Exception)
        assert error.message == "Recording failed"
        assert error.camera_id == "CAM999"


@pytest.mark.unit
class TestEncoderExceptions:
    """Test encoder exception classes."""
    
    def test_encoder_error_basic(self):
        """Test basic EncoderError creation."""
        error = EncoderError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.encoder_id is None
        assert error.error_type is None
        assert isinstance(error, Exception)
    
    def test_encoder_error_with_encoder_id(self):
        """Test EncoderError with encoder ID."""
        error = EncoderError("Encoder not found", encoder_id="ENC123")
        
        assert error.message == "Encoder not found"
        assert error.encoder_id == "ENC123"
        assert error.error_type is None
    
    def test_encoder_error_with_all_params(self):
        """Test EncoderError with all parameters."""
        error = EncoderError(
            "Operation failed",
            encoder_id="ENC456",
            error_type="api_error"
        )
        
        assert error.message == "Operation failed"
        assert error.encoder_id == "ENC456"
        assert error.error_type == "api_error"
    
    def test_encoder_connection_error(self):
        """Test EncoderConnectionError."""
        error = EncoderConnectionError("Connection failed", encoder_id="ENC789")
        
        assert isinstance(error, EncoderError)
        assert isinstance(error, Exception)
        assert error.message == "Connection failed"
        assert error.encoder_id == "ENC789"
    
    def test_encoder_recording_error(self):
        """Test EncoderRecordingError."""
        error = EncoderRecordingError("Recording failed", encoder_id="ENC999")
        
        assert isinstance(error, EncoderError)
        assert isinstance(error, Exception)
        assert error.message == "Recording failed"
        assert error.encoder_id == "ENC999"


@pytest.mark.unit
class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""
    
    def test_arlo_exception_hierarchy(self):
        """Test that Arlo exceptions inherit correctly."""
        connection_error = ArloConnectionError("Test")
        camera_error = ArloCameraError("Test")
        recording_error = ArloRecordingError("Test")
        
        # All should be ArloError
        assert isinstance(connection_error, ArloError)
        assert isinstance(camera_error, ArloError)
        assert isinstance(recording_error, ArloError)
        
        # All should be Exception
        assert isinstance(connection_error, Exception)
        assert isinstance(camera_error, Exception)
        assert isinstance(recording_error, Exception)
    
    def test_encoder_exception_hierarchy(self):
        """Test that encoder exceptions inherit correctly."""
        connection_error = EncoderConnectionError("Test")
        recording_error = EncoderRecordingError("Test")
        
        # All should be EncoderError
        assert isinstance(connection_error, EncoderError)
        assert isinstance(recording_error, EncoderError)
        
        # All should be Exception
        assert isinstance(connection_error, Exception)
        assert isinstance(recording_error, Exception)
    
    def test_exception_can_be_raised(self):
        """Test that exceptions can be raised and caught."""
        with pytest.raises(ArloError) as exc_info:
            raise ArloError("Test error")
        
        assert str(exc_info.value) == "Test error"
        assert exc_info.value.message == "Test error"
    
    def test_exception_can_be_caught_by_base(self):
        """Test that specific exceptions can be caught by base class."""
        with pytest.raises(ArloError):
            raise ArloConnectionError("Connection failed")
        
        with pytest.raises(EncoderError):
            raise EncoderConnectionError("Connection failed")

