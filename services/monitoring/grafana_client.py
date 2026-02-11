"""Grafana API client."""

from typing import Optional, Dict, List, Any
import base64
from services.base import BaseServiceClient
from services.monitoring.config import GrafanaConfig
from app.exceptions import GrafanaError


class GrafanaClient(BaseServiceClient):
    """Client for interacting with Grafana API."""
    
    def __init__(self, config: Optional[GrafanaConfig] = None):
        self.config = config or GrafanaConfig()
        self.api_key = self.config.api_key
        super().__init__(self.config.base_url)
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for Grafana (Bearer token or Basic auth)."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            # Use basic auth if no API key
            auth_string = f"{self.config.username}:{self.config.password}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            headers["Authorization"] = f"Basic {auth_b64}"
        return headers
    
    def _get_api_base_url(self) -> str:
        """Get Grafana API base URL."""
        return f"{self.base_url}/api"
    
    def _get_ping_endpoint(self) -> str:
        """Get Grafana health check endpoint."""
        return "/api/health"
    
    async def get_dashboards(self) -> List[Dict[str, Any]]:
        """Get list of dashboards."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get("/search", params={"type": "dash-db"}),
            "get_dashboards",
            default_return=[]
        )
        return result if isinstance(result, list) else []
    
    async def get_dashboard(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get a specific dashboard."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get(f"/dashboards/uid/{uid}"),
            "get_dashboard",
            default_return=None,
            raise_on_error=True,
            exception_class=GrafanaError
        )
        return result
    
    async def get_datasources(self) -> List[Dict[str, Any]]:
        """Get list of datasources."""
        await self._ensure_session()
        
        result = await self._handle_request(
            lambda: self._session.get("/datasources"),
            "get_datasources",
            default_return=[]
        )
        return result if isinstance(result, list) else []


