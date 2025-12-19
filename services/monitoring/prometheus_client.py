"""Prometheus API client."""

import httpx
from typing import Optional, Dict, List, Any
from services.monitoring.config import PrometheusConfig


class PrometheusClient:
    """Client for interacting with Prometheus API."""
    
    def __init__(self, config: Optional[PrometheusConfig] = None):
        self.config = config or PrometheusConfig()
        self.base_url = self.config.base_url.rstrip('/')
        self._session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._session = httpx.AsyncClient(
            base_url=f"{self.base_url}/api/v1",
            timeout=30.0
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.aclose()
    
    async def ping(self) -> bool:
        """Check if Prometheus is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/-/healthy")
                return response.status_code == 200
        except Exception:
            return False
    
    async def query(self, query: str) -> Optional[Dict[str, Any]]:
        """Execute a PromQL query."""
        if not self._session:
            async with self:
                return await self.query(query)
        
        try:
            response = await self._session.get(
                "/query",
                params={"query": query}
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    async def query_range(self, query: str, start: str, end: str, step: str = "15s") -> Optional[Dict[str, Any]]:
        """Execute a range query."""
        if not self._session:
            async with self:
                return await self.query_range(query, start, end, step)
        
        try:
            response = await self._session.get(
                "/query_range",
                params={
                    "query": query,
                    "start": start,
                    "end": end,
                    "step": step
                }
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    async def get_targets(self) -> Optional[Dict[str, Any]]:
        """Get list of targets."""
        if not self._session:
            async with self:
                return await self.get_targets()
        
        try:
            response = await self._session.get("/targets")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    async def get_metrics(self) -> List[str]:
        """Get list of available metrics."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/v1/label/__name__/values")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
        except Exception:
            pass
        return []


