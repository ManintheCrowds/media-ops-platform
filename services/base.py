"""Base service client for HTTP API clients.

PURPOSE: Provides common functionality for all service clients including
session management, ping(), and standardized exception handling.

DEPENDENCIES: httpx, logging, abc, typing

MODIFICATION NOTES: v1.0 - Initial implementation to eliminate code duplication
"""

import httpx
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, Awaitable

logger = logging.getLogger(__name__)


class BaseServiceClient(ABC):
    """Abstract base class for service API clients.
    
    Provides common functionality:
    - Async context manager (__aenter__, __aexit__)
    - Session management with auto-creation
    - Standardized ping() method
    - Common exception handling with logging
    """
    
    def __init__(self, base_url: str):
        """Initialize the service client.
        
        Args:
            base_url: Base URL for the service (will be normalized)
        """
        self.base_url = base_url.rstrip('/')
        self._session: Optional[httpx.AsyncClient] = None
    
    @abstractmethod
    def _build_headers(self) -> Dict[str, str]:
        """Build authentication headers for the service.
        
        Returns:
            Dictionary of HTTP headers to include in requests
        """
        pass
    
    @abstractmethod
    def _get_api_base_url(self) -> str:
        """Get the API base URL for session creation.
        
        This is the URL that will be used as the base_url for the httpx.AsyncClient.
        It may include path prefixes like /api/v1.
        
        Returns:
            Full base URL including any path prefixes
        """
        pass
    
    @abstractmethod
    def _get_ping_endpoint(self) -> str:
        """Get the endpoint path for ping/health checks.
        
        Returns:
            Endpoint path (e.g., "/health", "/-/healthy", "/")
        """
        pass
    
    async def __aenter__(self):
        """Async context manager entry - creates session."""
        headers = self._build_headers()
        api_base_url = self._get_api_base_url()
        
        self._session = httpx.AsyncClient(
            base_url=api_base_url,
            timeout=30.0,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - closes session."""
        if self._session:
            await self._session.aclose()
            self._session = None
    
    async def _ensure_session(self):
        """Ensure session exists, creating it if necessary."""
        if not self._session:
            await self.__aenter__()
    
    async def ping(self) -> bool:
        """Check if the service is accessible.
        
        Returns:
            True if service is reachable and healthy, False otherwise
        """
        ping_endpoint = self._get_ping_endpoint()
        full_url = f"{self.base_url}{ping_endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(full_url)
                return response.status_code == 200
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error in {self.__class__.__name__}.ping(): {e}")
            return False
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout in {self.__class__.__name__}.ping(): {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in {self.__class__.__name__}.ping(): {e}", exc_info=True)
            return False
    
    async def _handle_request(
        self,
        method: Callable[[], Awaitable[httpx.Response]],
        method_name: str,
        default_return: Any = None,
        raise_on_error: bool = False,
        exception_class: Optional[type] = None
    ) -> Any:
        """Handle a request with standardized exception handling.
        
        Args:
            method: Async callable that returns an httpx.Response
            method_name: Name of the method for logging (e.g., "get_dashboards")
            default_return: Value to return on error (None, [], False, etc.)
            raise_on_error: If True, raise exceptions instead of returning default_return
            exception_class: Exception class to raise (must be ServiceError subclass)
        
        Returns:
            Response data (JSON parsed) or default_return on error (if raise_on_error=False)
        
        Raises:
            ServiceError or subclass if raise_on_error=True
        """
        try:
            response = await method()
            if response.status_code == 200:
                return response.json()
            elif response.status_code in (201, 204):
                # Some APIs return 201/204 for successful creation
                try:
                    return response.json()
                except Exception:
                    return {"status": "success"}
            else:
                error_msg = f"Non-200 status in {self.__class__.__name__}.{method_name}(): {response.status_code}"
                logger.warning(error_msg)
                if raise_on_error:
                    from app.exceptions import ServiceError
                    exc_class = exception_class or ServiceError
                    raise exc_class(
                        message=error_msg,
                        status_code=response.status_code,
                        error_code="HTTP_ERROR"
                    )
                return default_return
        except httpx.HTTPError as e:
            error_msg = f"HTTP error in {self.__class__.__name__}.{method_name}(): {e}"
            logger.warning(error_msg)
            if raise_on_error:
                from app.exceptions import ServiceError
                exc_class = exception_class or ServiceError
                raise exc_class(
                    message=str(e),
                    status_code=500,
                    error_code="HTTP_ERROR"
                )
            return default_return
        except httpx.TimeoutException as e:
            error_msg = f"Timeout in {self.__class__.__name__}.{method_name}(): {e}"
            logger.warning(error_msg)
            if raise_on_error:
                from app.exceptions import ServiceError
                exc_class = exception_class or ServiceError
                raise exc_class(
                    message=str(e),
                    status_code=503,
                    error_code="TIMEOUT_ERROR"
                )
            return default_return
        except Exception as e:
            error_msg = f"Unexpected error in {self.__class__.__name__}.{method_name}(): {e}"
            logger.error(error_msg, exc_info=True)
            if raise_on_error:
                # Re-raise if it's already a ServiceError
                from app.exceptions import ServiceError
                if isinstance(e, ServiceError):
                    raise
                exc_class = exception_class or ServiceError
                raise exc_class(
                    message=str(e),
                    status_code=500,
                    error_code="INTERNAL_ERROR"
                )
            return default_return

