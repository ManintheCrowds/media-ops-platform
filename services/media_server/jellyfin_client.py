"""Jellyfin API client."""

import httpx
from typing import Optional, Dict, List, Any
from services.media_server.config import JellyfinConfig


class JellyfinClient:
    """Client for interacting with Jellyfin API."""
    
    def __init__(self, config: Optional[JellyfinConfig] = None):
        self.config = config or JellyfinConfig()
        self.base_url = self.config.base_url.rstrip('/')
        self.api_key = self.config.api_key
        self._session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        headers = {
            "X-Emby-Authorization": f"MediaBrowser Client=\"Platform\", Device=\"Server\", DeviceId=\"platform\", Version=\"1.0.0\""
        }
        if self.api_key:
            headers["X-Emby-Token"] = self.api_key
        
        self._session = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.aclose()
    
    async def ping(self) -> bool:
        """Check if Jellyfin is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/System/Ping")
                return response.status_code == 200
        except Exception:
            return False
    
    async def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate and get API key."""
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
        except Exception:
            pass
        return None
    
    async def get_server_info(self) -> Optional[Dict[str, Any]]:
        """Get server information."""
        if not self._session:
            async with self:
                return await self.get_server_info()
        
        try:
            response = await self._session.get("/System/Info")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    async def get_libraries(self) -> List[Dict[str, Any]]:
        """Get list of libraries."""
        if not self._session:
            async with self:
                return await self.get_libraries()
        
        try:
            response = await self._session.get("/Library/VirtualFolders")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []
    
    async def get_recent_items(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently added items."""
        if not self._session:
            async with self:
                return await self.get_recent_items(limit)
        
        try:
            response = await self._session.get(
                "/Items/Latest",
                params={"Limit": limit}
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []


