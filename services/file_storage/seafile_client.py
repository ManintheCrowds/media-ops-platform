"""Seafile API client."""

import httpx
import logging
from typing import Optional, Dict, List, Any
from services.base import BaseServiceClient
from services.file_storage.config import SeafileConfig
from app.exceptions import SeafileError

logger = logging.getLogger(__name__)


class SeafileClient(BaseServiceClient):
    """Client for interacting with Seafile API."""
    
    def __init__(self, config: Optional[SeafileConfig] = None):
        self.config = config or SeafileConfig()
        self.api_token = self.config.api_token
        super().__init__(self.config.base_url)
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for Seafile API."""
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Token {self.api_token}"
        return headers
    
    def _get_api_base_url(self) -> str:
        """Get Seafile API base URL."""
        return self.base_url
    
    def _get_ping_endpoint(self) -> str:
        """Get Seafile health check endpoint."""
        return "/api2/ping/"
    
    async def get_auth_token(self, username: str, password: str) -> Optional[str]:
        """Get authentication token."""
        # This method doesn't use the session, so we handle it separately
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api2/auth-token/",
                    data={"username": username, "password": password}
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("token")
                elif response.status_code == 401:
                    raise SeafileError("Authentication failed: invalid credentials", status_code=401, error_code="AUTH_ERROR")
                else:
                    raise SeafileError(f"Failed to get auth token: HTTP {response.status_code}")
        except SeafileError:
            raise
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error in {self.__class__.__name__}.get_auth_token(): {e}")
            raise SeafileError(f"HTTP error while getting auth token: {e}")
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout in {self.__class__.__name__}.get_auth_token(): {e}")
            raise SeafileError(f"Timeout while getting auth token: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in {self.__class__.__name__}.get_auth_token(): {e}", exc_info=True)
            raise SeafileError(f"Unexpected error while getting auth token: {e}")
    
    async def get_libraries(self) -> List[Dict[str, Any]]:
        """Get list of libraries."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get("/api2/repos/"),
            "get_libraries",
            default_return=[]
        )
        return result if isinstance(result, list) else []
    
    async def get_library_info(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get library information."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get(f"/api2/repos/{repo_id}/"),
            "get_library_info",
            default_return=None,
            raise_on_error=True,
            exception_class=SeafileError
        )
        return result
    
    async def create_library(self, name: str, description: str = "") -> Optional[Dict[str, Any]]:
        """Create a new library."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.post(
                "/api2/repos/",
                json={"name": name, "desc": description}
            ),
            "create_library",
            default_return=None,
            raise_on_error=True,
            exception_class=SeafileError
        )
        return result


