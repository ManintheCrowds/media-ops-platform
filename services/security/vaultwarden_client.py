"""Vaultwarden API client."""

import httpx
from typing import Optional, Dict, List, Any
from services.security.config import VaultwardenConfig


class VaultwardenClient:
    """Client for interacting with Vaultwarden API."""
    
    def __init__(self, config: Optional[VaultwardenConfig] = None):
        self.config = config or VaultwardenConfig()
        self.base_url = self.config.base_url.rstrip('/')
        self.admin_token = self.config.admin_token
        self._session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        headers = {}
        if self.admin_token:
            headers["X-Vaultwarden-Admin-Token"] = self.admin_token
        
        self._session = httpx.AsyncClient(
            base_url=f"{self.base_url}/admin",
            timeout=30.0,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.aclose()
    
    async def ping(self) -> bool:
        """Check if Vaultwarden is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/")
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get list of users (admin only)."""
        if not self._session:
            async with self:
                return await self.get_users()
        
        try:
            response = await self._session.get("/users")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information (admin only)."""
        if not self._session:
            async with self:
                return await self.get_user(user_id)
        
        try:
            response = await self._session.get(f"/users/{user_id}")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    async def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get Vaultwarden statistics (admin only)."""
        if not self._session:
            async with self:
                return await self.get_stats()
        
        try:
            response = await self._session.get("/stats")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None


