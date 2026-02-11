"""Jellyfin API client."""

import httpx
import logging
from typing import Optional, Dict, List, Any
from services.base import BaseServiceClient
from services.media_server.config import JellyfinConfig
from app.exceptions import JellyfinError

logger = logging.getLogger(__name__)


class JellyfinClient(BaseServiceClient):
    """Client for interacting with Jellyfin API."""
    
    def __init__(self, config: Optional[JellyfinConfig] = None):
        self.config = config or JellyfinConfig()
        self.api_key = self.config.api_key
        super().__init__(self.config.base_url)
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for Jellyfin API."""
        headers = {
            "X-Emby-Authorization": "MediaBrowser Client=\"Platform\", Device=\"Server\", DeviceId=\"platform\", Version=\"1.0.0\""
        }
        if self.api_key:
            headers["X-Emby-Token"] = self.api_key
        return headers
    
    def _get_api_base_url(self) -> str:
        """Get Jellyfin API base URL."""
        return self.base_url
    
    def _get_ping_endpoint(self) -> str:
        """Get Jellyfin health check endpoint."""
        return "/System/Ping"
    
    async def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate and get API key."""
        # This method doesn't use the session, so we handle it separately
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/Users/authenticatebyname",
                    json={"Username": username, "Pw": password},
                    headers={
                        "X-Emby-Authorization": "MediaBrowser Client=\"Platform\", Device=\"Server\", DeviceId=\"platform\", Version=\"1.0.0\""
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("AccessToken")
                elif response.status_code == 401:
                    raise JellyfinError("Authentication failed: invalid credentials", status_code=401, error_code="AUTH_ERROR")
                else:
                    raise JellyfinError(f"Failed to authenticate: HTTP {response.status_code}")
        except JellyfinError:
            raise
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error in {self.__class__.__name__}.authenticate(): {e}")
            raise JellyfinError(f"HTTP error while authenticating: {e}")
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout in {self.__class__.__name__}.authenticate(): {e}")
            raise JellyfinError(f"Timeout while authenticating: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in {self.__class__.__name__}.authenticate(): {e}", exc_info=True)
            raise JellyfinError(f"Unexpected error while authenticating: {e}")
    
    async def get_server_info(self) -> Optional[Dict[str, Any]]:
        """Get server information."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get("/System/Info"),
            "get_server_info",
            default_return=None,
            raise_on_error=True,
            exception_class=JellyfinError
        )
        return result
    
    async def get_libraries(self) -> List[Dict[str, Any]]:
        """Get list of libraries."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get("/Library/VirtualFolders"),
            "get_libraries",
            default_return=[]
        )
        return result if isinstance(result, list) else []
    
    async def get_recent_items(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently added items."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get(
                "/Items/Latest",
                params={"Limit": limit}
            ),
            "get_recent_items",
            default_return=[]
        )
        return result if isinstance(result, list) else []


