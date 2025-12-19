"""Seafile integration client."""

import httpx
from typing import Optional, Dict, Any
from app.config import settings


class SeafileClient:
    """Client for Seafile API integration."""
    
    def __init__(self):
        self.base_url = settings.seafile_url.rstrip('/')
        self.api_token = settings.seafile_api_token
        self._session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Token {self.api_token}"
        
        self._session = httpx.AsyncClient(
            base_url=f"{self.base_url}/api2",
            timeout=30.0,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.aclose()
    
    async def get_library(self, library_id: str) -> Optional[Dict[str, Any]]:
        """Get a Seafile library by ID."""
        try:
            response = await self._session.get(f"/repos/{library_id}")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    async def get_file_info(self, library_id: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file information from Seafile."""
        try:
            response = await self._session.get(
                f"/repos/{library_id}/file/detail",
                params={"p": file_path}
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

