"""Prometheus API client."""

from typing import Optional, Dict, List, Any
from services.base import BaseServiceClient
from services.monitoring.config import PrometheusConfig


class PrometheusClient(BaseServiceClient):
    """Client for interacting with Prometheus API."""
    
    def __init__(self, config: Optional[PrometheusConfig] = None):
        self.config = config or PrometheusConfig()
        super().__init__(self.config.base_url)
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for Prometheus (no authentication required)."""
        return {}
    
    def _get_api_base_url(self) -> str:
        """Get Prometheus API base URL."""
        return f"{self.base_url}/api/v1"
    
    def _get_ping_endpoint(self) -> str:
        """Get Prometheus health check endpoint."""
        return "/-/healthy"
    
    async def query(self, query: str) -> Optional[Dict[str, Any]]:
        """Execute a PromQL query."""
        await self._ensure_session()
        
        return await self._handle_request(
            lambda: self._session.get("/query", params={"query": query}),
            "query",
            default_return=None
        )
    
    async def query_range(self, query: str, start: str, end: str, step: str = "15s") -> Optional[Dict[str, Any]]:
        """Execute a range query."""
        await self._ensure_session()
        
        return await self._handle_request(
            lambda: self._session.get(
                "/query_range",
                params={
                    "query": query,
                    "start": start,
                    "end": end,
                    "step": step
                }
            ),
            "query_range",
            default_return=None
        )
    
    async def get_targets(self) -> Optional[Dict[str, Any]]:
        """Get list of targets."""
        await self._ensure_session()
        
        return await self._handle_request(
            lambda: self._session.get("/targets"),
            "get_targets",
            default_return=None
        )
    
    async def get_metrics(self) -> List[str]:
        """Get list of available metrics."""
        # This method doesn't use the session, so we handle it separately
        import httpx
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/v1/label/__name__/values")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error in {self.__class__.__name__}.get_metrics(): {e}")
            return []
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout in {self.__class__.__name__}.get_metrics(): {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in {self.__class__.__name__}.get_metrics(): {e}", exc_info=True)
            return []


