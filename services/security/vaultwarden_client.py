"""Vaultwarden API client."""

from typing import Optional, Dict, List, Any
from services.base import BaseServiceClient
from services.security.config import VaultwardenConfig
from app.exceptions import VaultwardenError


class VaultwardenClient(BaseServiceClient):
    """Client for interacting with Vaultwarden API."""
    
    def __init__(self, config: Optional[VaultwardenConfig] = None):
        self.config = config or VaultwardenConfig()
        self.admin_token = self.config.admin_token
        super().__init__(self.config.base_url)
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for Vaultwarden admin API."""
        headers = {}
        if self.admin_token:
            headers["X-Vaultwarden-Admin-Token"] = self.admin_token
        return headers
    
    def _get_api_base_url(self) -> str:
        """Get Vaultwarden admin API base URL."""
        return f"{self.base_url}/admin"
    
    def _get_ping_endpoint(self) -> str:
        """Get Vaultwarden health check endpoint."""
        return "/"
    
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get list of users (admin only)."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get("/users"),
            "get_users",
            default_return=[]
        )
        return result if isinstance(result, list) else []
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information (admin only)."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get(f"/users/{user_id}"),
            "get_user",
            default_return=None,
            raise_on_error=True,
            exception_class=VaultwardenError
        )
        return result
    
    async def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get Vaultwarden statistics (admin only)."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get("/stats"),
            "get_stats",
            default_return=None,
            raise_on_error=True,
            exception_class=VaultwardenError
        )
        return result


