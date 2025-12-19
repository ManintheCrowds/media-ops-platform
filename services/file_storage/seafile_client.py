"""Seafile API client."""

import httpx
from typing import Optional, Dict, List, Any
from services.file_storage.config import SeafileConfig


class SeafileClient:
    """Client for interacting with Seafile API."""
    
    def __init__(self, config: Optional[SeafileConfig] = None):
        self.config = config or SeafileConfig()
        self.base_url = self.config.base_url.rstrip('/')
        self.api_token = self.config.api_token
        self._session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._session = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={"Authorization": f"Token {self.api_token}"} if self.api_token else {}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.aclose()
    
    async def ping(self) -> bool:
        """Check if Seafile is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api2/ping/")
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_auth_token(self, username: str, password: str) -> Optional[str]:
        """Get authentication token."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api2/auth-token/",
                    data={"username": username, "password": password}
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("token")
        except Exception:
            pass
        return None
    
    async def get_libraries(self) -> List[Dict[str, Any]]:
        """Get list of libraries."""
        if not self._session:
            async with self:
                return await self.get_libraries()
        
        try:
            response = await self._session.get("/api2/repos/")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []
    
    async def get_library_info(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get library information."""
        if not self._session:
            async with self:
                return await self.get_library_info(repo_id)
        
        try:
            response = await self._session.get(f"/api2/repos/{repo_id}/")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    async def create_library(self, name: str, description: str = "") -> Optional[Dict[str, Any]]:
        """Create a new library."""
        if not self._session:
            async with self:
                return await self.create_library(name, description)
        
        try:
            response = await self._session.post(
                "/api2/repos/",
                json={"name": name, "desc": description}
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None


