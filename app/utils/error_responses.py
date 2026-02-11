"""Standardized error response utilities for API endpoints."""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: str


def create_error_response(
    error: str,
    status_code: int,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized error response.
    
    Args:
        error: Human-readable error message
        status_code: HTTP status code
        error_code: Optional machine-readable error code
        details: Optional additional error details
        
    Returns:
        JSONResponse with standardized error format
    """
    error_response = ErrorResponse(
        error=error,
        error_code=error_code,
        details=details,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(exclude_none=True)
    )


def convert_to_http_exception(
    exception: Exception,
    default_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    error_code: Optional[str] = None
) -> HTTPException:
    """Convert an exception to an HTTPException with standardized format.
    
    Args:
        exception: Exception to convert
        default_status: Default HTTP status code if exception doesn't have one
        error_code: Optional machine-readable error code
        
    Returns:
        HTTPException with standardized error detail
    """
    # Check if exception has status_code attribute (custom exceptions)
    status_code = getattr(exception, 'status_code', default_status)
    
    # Get error message
    if hasattr(exception, 'message'):
        error_msg = exception.message
    elif hasattr(exception, 'detail'):
        error_msg = exception.detail
    else:
        error_msg = str(exception)
    
    # Get error code from exception if available
    if not error_code and hasattr(exception, 'error_code'):
        error_code = exception.error_code
    
    # Create standardized error detail
    error_detail = {
        "error": error_msg,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
    
    if error_code:
        error_detail["error_code"] = error_code
    
    if hasattr(exception, 'details'):
        error_detail["details"] = exception.details
    
    return HTTPException(
        status_code=status_code,
        detail=error_detail
    )


def handle_service_error(exception: Exception) -> JSONResponse:
    """Handle service errors and return standardized JSON response.
    
    Args:
        exception: Exception to handle
        
    Returns:
        JSONResponse with standardized error format
    """
    # Map exception types to status codes
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = None
    
    if hasattr(exception, 'status_code'):
        status_code = exception.status_code
    elif isinstance(exception, ValueError):
        status_code = status.HTTP_400_BAD_REQUEST
        error_code = "VALIDATION_ERROR"
    elif isinstance(exception, PermissionError):
        status_code = status.HTTP_403_FORBIDDEN
        error_code = "PERMISSION_DENIED"
    elif isinstance(exception, FileNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
        error_code = "NOT_FOUND"
    elif isinstance(exception, ConnectionError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        error_code = "SERVICE_UNAVAILABLE"
    
    # Get error message
    if hasattr(exception, 'message'):
        error_msg = exception.message
    else:
        error_msg = str(exception)
    
    # Get error code from exception if available
    if hasattr(exception, 'error_code'):
        error_code = exception.error_code
    
    # Get details if available
    details = None
    if hasattr(exception, 'details'):
        details = exception.details
    elif hasattr(exception, 'camera_id') or hasattr(exception, 'encoder_id'):
        details = {}
        if hasattr(exception, 'camera_id'):
            details['camera_id'] = exception.camera_id
        if hasattr(exception, 'encoder_id'):
            details['encoder_id'] = exception.encoder_id
        if hasattr(exception, 'error_type'):
            details['error_type'] = exception.error_type
    
    return create_error_response(
        error=error_msg,
        status_code=status_code,
        error_code=error_code,
        details=details
    )


# Standard error codes
class ErrorCodes:
    """Standard error codes for consistent error handling."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    ARLO_ERROR = "ARLO_ERROR"
    ARLO_CONNECTION_ERROR = "ARLO_CONNECTION_ERROR"
    ARLO_CAMERA_ERROR = "ARLO_CAMERA_ERROR"
    ARLO_RECORDING_ERROR = "ARLO_RECORDING_ERROR"
    ENCODER_ERROR = "ENCODER_ERROR"
    ENCODER_CONNECTION_ERROR = "ENCODER_CONNECTION_ERROR"
    ENCODER_RECORDING_ERROR = "ENCODER_RECORDING_ERROR"

