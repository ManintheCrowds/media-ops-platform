"""Custom exceptions for camera and encoder services."""

from typing import Optional


class ArloError(Exception):
    """Base class for Arlo-related errors."""
    def __init__(self, message: str, camera_id: Optional[str] = None, error_type: Optional[str] = None):
        self.message = message
        self.camera_id = camera_id
        self.error_type = error_type
        super().__init__(self.message)


class ArloConnectionError(ArloError):
    """Exception raised for Arlo connection or authentication errors."""
    pass


class ArloCameraError(ArloError):
    """Exception raised for camera-specific operation errors."""
    pass


class ArloRecordingError(ArloError):
    """Exception raised for Arlo recording management errors."""
    pass


class EncoderError(Exception):
    """Base class for encoder-related errors."""
    def __init__(self, message: str, encoder_id: Optional[str] = None, error_type: Optional[str] = None):
        self.message = message
        self.encoder_id = encoder_id
        self.error_type = error_type
        super().__init__(self.message)


class EncoderConnectionError(EncoderError):
    """Exception raised for encoder connection errors."""
    pass


class EncoderRecordingError(EncoderError):
    """Exception raised for encoder recording errors."""
    pass

