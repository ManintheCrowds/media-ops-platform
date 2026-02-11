"""Custom exceptions for camera and encoder services."""

from typing import Optional, Dict, Any
from fastapi import status


class ServiceError(Exception):
    """Base class for all service errors with HTTP status code mapping."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ArloError(ServiceError):
    """Base class for Arlo-related errors."""
    def __init__(
        self,
        message: str,
        camera_id: Optional[str] = None,
        error_type: Optional[str] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None
    ):
        details = {}
        if camera_id:
            details['camera_id'] = camera_id
        if error_type:
            details['error_type'] = error_type
        
        error_code = error_code or "ARLO_ERROR"
        super().__init__(message, status_code, error_code, details)
        self.camera_id = camera_id
        self.error_type = error_type


class ArloConnectionError(ArloError):
    """Exception raised for Arlo connection or authentication errors."""
    def __init__(
        self,
        message: str,
        camera_id: Optional[str] = None,
        error_type: Optional[str] = None
    ):
        super().__init__(
            message,
            camera_id=camera_id,
            error_type=error_type,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="ARLO_CONNECTION_ERROR"
        )


class ArloCameraError(ArloError):
    """Exception raised for camera-specific operation errors."""
    def __init__(
        self,
        message: str,
        camera_id: Optional[str] = None,
        error_type: Optional[str] = None
    ):
        super().__init__(
            message,
            camera_id=camera_id,
            error_type=error_type,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="ARLO_CAMERA_ERROR"
        )


class ArloRecordingError(ArloError):
    """Exception raised for Arlo recording management errors."""
    def __init__(
        self,
        message: str,
        camera_id: Optional[str] = None,
        error_type: Optional[str] = None
    ):
        super().__init__(
            message,
            camera_id=camera_id,
            error_type=error_type,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="ARLO_RECORDING_ERROR"
        )


class EncoderError(ServiceError):
    """Base class for encoder-related errors."""
    def __init__(
        self,
        message: str,
        encoder_id: Optional[str] = None,
        error_type: Optional[str] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None
    ):
        details = {}
        if encoder_id:
            details['encoder_id'] = encoder_id
        if error_type:
            details['error_type'] = error_type
        
        error_code = error_code or "ENCODER_ERROR"
        super().__init__(message, status_code, error_code, details)
        self.encoder_id = encoder_id
        self.error_type = error_type


class EncoderConnectionError(EncoderError):
    """Exception raised for encoder connection errors."""
    def __init__(
        self,
        message: str,
        encoder_id: Optional[str] = None,
        error_type: Optional[str] = None
    ):
        super().__init__(
            message,
            encoder_id=encoder_id,
            error_type=error_type,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="ENCODER_CONNECTION_ERROR"
        )


class EncoderRecordingError(EncoderError):
    """Exception raised for encoder recording errors."""
    def __init__(
        self,
        message: str,
        encoder_id: Optional[str] = None,
        error_type: Optional[str] = None
    ):
        super().__init__(
            message,
            encoder_id=encoder_id,
            error_type=error_type,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="ENCODER_RECORDING_ERROR"
        )


# Additional service error classes for other services
class VaultwardenError(ServiceError):
    """Exception raised for Vaultwarden service errors."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None
    ):
        error_code = error_code or "VAULTWARDEN_ERROR"
        super().__init__(message, status_code, error_code)


class WikiError(ServiceError):
    """Exception raised for Wiki (BookStack) service errors."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None
    ):
        error_code = error_code or "WIKI_ERROR"
        super().__init__(message, status_code, error_code)


class SeafileError(ServiceError):
    """Exception raised for Seafile service errors."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None
    ):
        error_code = error_code or "SEAFILE_ERROR"
        super().__init__(message, status_code, error_code)


class JellyfinError(ServiceError):
    """Exception raised for Jellyfin service errors."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None
    ):
        error_code = error_code or "JELLYFIN_ERROR"
        super().__init__(message, status_code, error_code)


class GiteaError(ServiceError):
    """Exception raised for Gitea service errors."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None
    ):
        error_code = error_code or "GITEA_ERROR"
        super().__init__(message, status_code, error_code)


class GrafanaError(ServiceError):
    """Exception raised for Grafana service errors."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None
    ):
        error_code = error_code or "GRAFANA_ERROR"
        super().__init__(message, status_code, error_code)


class PrometheusError(ServiceError):
    """Exception raised for Prometheus service errors."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None
    ):
        error_code = error_code or "PROMETHEUS_ERROR"
        super().__init__(message, status_code, error_code)

