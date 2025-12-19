"""Grafana API client."""

import httpx
from typing import Optional, Dict, List, Any
from services.monitoring.config import GrafanaConfig


class GrafanaClient:
    """Client for interacting with Grafana API."""
    
    def __init__(self, config: Optional[GrafanaConfig] = None):
        self.config = config or GrafanaConfig()
        self.base_url = self.config.base_url.rstrip('/')
        self.api_key = self.config.api_key
        self._session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            # Use basic auth if no API key
            import base64
            auth_string = f"{self.config.username}:{self.config.password}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            headers["Authorization"] = f"Basic {auth_b64}"
        
        self._session = httpx.AsyncClient(
            base_url=f"{self.base_url}/api",
            timeout=30.0,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.aclose()
    
    async def ping(self) -> bool:
        """Check if Grafana is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/health")
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_dashboards(self) -> List[Dict[str, Any]]:
        """Get list of dashboards."""
        if not self._session:
            async with self:
                return await self.get_dashboards()
        
        try:
            response = await self._session.get("/search", params={"type": "dash-db"})
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []
    
    async def get_dashboard(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get a specific dashboard."""
        if not self._session:
            async with self:
                return await self.get_dashboard(uid)
        
        try:
            response = await self._session.get(f"/dashboards/uid/{uid}")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    async def get_datasources(self) -> List[Dict[str, Any]]:
        """Get list of datasources."""
        if not self._session:
            async with self:
                return await self.get_datasources()
        
        try:
            response = await self._session.get("/datasources")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []


