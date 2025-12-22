"""Jellyfin integration client."""

import httpx
from typing import Optional, Dict, Any
from app.config import settings


class JellyfinClient:
    """Client for Jellyfin API integration."""
    
    def __init__(self):
        self.base_url = settings.jellyfin_url.rstrip('/')
        self.api_key = settings.jellyfin_api_key
        self._session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        headers = {
            "X-Emby-Authorization": "MediaBrowser Client=\"EducationService\", Device=\"Server\", DeviceId=\"education\", Version=\"1.0.0\""
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
    
    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get a Jellyfin media item by ID."""
        try:
            response = await self._session.get(f"/Items/{item_id}")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    async def get_stream_url(self, item_id: str) -> Optional[str]:
        """Get streaming URL for a media item."""
        try:
            response = await self._session.get(f"/Items/{item_id}/Download")
            if response.status_code == 200:
                # Return the URL for streaming
                return f"{self.base_url}/Items/{item_id}/Download?api_key={self.api_key}"
        except Exception:
            pass
        return None




