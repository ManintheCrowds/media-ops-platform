"""API client library for Pi client."""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
import httpx
from .config import Config

logger = logging.getLogger(__name__)


class PiAPIClient:
    """Lightweight HTTP client for Pi device API."""
    
    def __init__(self, config: Config):
        """Initialize API client."""
        self.config = config
        self.base_url = config.api.base_url.rstrip("/")
        self.api_base = f"{self.base_url}/api/v1/pi"
        self.auth_token = config.api.auth_token
        self.timeout = config.api.timeout
        self.retry_attempts = config.api.retry_attempts
        
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "User-Agent": "Pi-Client/1.0",
        }
        
        self._client = httpx.AsyncClient(
            base_url=self.api_base,
            timeout=self.timeout,
            headers=headers,
            follow_redirects=True,
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        url = endpoint if endpoint.startswith("http") else f"{self.api_base}/{endpoint.lstrip('/')}"
        
        last_exception = None
        for attempt in range(self.retry_attempts):
            try:
                response = await self._client.request(method, url, **kwargs)
                
                # Handle token refresh if needed
                if response.status_code == 401:
                    logger.warning("Authentication failed, token may need refresh")
                    # Token refresh would be implemented here
                
                response.raise_for_status()
                return response
                
            except httpx.HTTPError as e:
                last_exception = e
                if attempt < self.retry_attempts - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.retry_attempts} attempts: {e}")
                    raise
        
        raise last_exception
    
    async def authenticate(self) -> Dict[str, Any]:
        """Authenticate device and get token."""
        # This would implement device authentication
        # For now, we assume token is provided in config
        return {"status": "authenticated", "token": self.auth_token}
    
    async def get_device(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Get device information."""
        device_id = device_id or self.config.device.device_id
        response = await self._request("GET", f"/devices/{device_id}")
        return response.json()
    
    async def update_device(self, device_id: Optional[str] = None, **updates) -> Dict[str, Any]:
        """Update device configuration."""
        device_id = device_id or self.config.device.device_id
        response = await self._request("PUT", f"/devices/{device_id}", json=updates)
        return response.json()
    
    async def get_device_status(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Get device sync status."""
        device_id = device_id or self.config.device.device_id
        response = await self._request("GET", f"/devices/{device_id}/status")
        return response.json()
    
    async def get_content_list(
        self,
        device_id: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch content list for device."""
        device_id = device_id or self.config.device.device_id
        params = {}
        if project_id:
            params["project_id"] = project_id
        
        response = await self._request("GET", f"/devices/{device_id}/content", params=params)
        return response.json()
    
    async def get_content_item(
        self,
        content_id: int,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch specific content item."""
        device_id = device_id or self.config.device.device_id
        response = await self._request("GET", f"/devices/{device_id}/content/{content_id}")
        return response.json()
    
    async def check_sync(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Check for available updates."""
        device_id = device_id or self.config.device.device_id
        response = await self._request("GET", f"/devices/{device_id}/sync/check")
        return response.json()
    
    async def request_sync(
        self,
        package_type: str = "incremental",
        content_ids: Optional[List[int]] = None,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Request sync package."""
        device_id = device_id or self.config.device.device_id
        params = {"package_type": package_type}
        if content_ids:
            params["content_ids"] = content_ids
        
        response = await self._request("POST", f"/devices/{device_id}/sync/request", params=params)
        return response.json()
    
    async def download_package(
        self,
        package_id: int,
        device_id: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """Download sync package."""
        import asyncio
        import aiofiles
        
        device_id = device_id or self.config.device.device_id
        response = await self._request("GET", f"/devices/{device_id}/sync/packages/{package_id}/download")
        
        if output_path is None:
            output_path = f"/tmp/package_{package_id}.tar.gz"
        
        async with aiofiles.open(output_path, "wb") as f:
            async for chunk in response.aiter_bytes():
                await f.write(chunk)
        
        return output_path
    
    async def stream_media(
        self,
        content_id: int,
        device_id: Optional[str] = None,
        start_byte: int = 0,
        end_byte: Optional[int] = None
    ) -> httpx.Response:
        """Stream media with range requests."""
        device_id = device_id or self.config.device.device_id
        headers = {}
        if start_byte > 0 or end_byte:
            range_header = f"bytes={start_byte}-"
            if end_byte:
                range_header = f"bytes={start_byte}-{end_byte}"
            headers["Range"] = range_header
        
        response = await self._request(
            "GET",
            f"/devices/{device_id}/content/{content_id}/stream",
            headers=headers
        )
        return response
    
    async def get_stream_info(
        self,
        content_id: int,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stream metadata."""
        device_id = device_id or self.config.device.device_id
        response = await self._request("GET", f"/devices/{device_id}/content/{content_id}/stream/info")
        return response.json()
    
    async def get_display_config(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Get display configuration."""
        device_id = device_id or self.config.device.device_id
        response = await self._request("GET", f"/devices/{device_id}/display/config")
        return response.json()
    
    async def submit_sensor_data(
        self,
        sensor_type: str,
        value: float,
        unit: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit sensor data."""
        device_id = device_id or self.config.device.device_id
        data = {
            "sensor_type": sensor_type,
            "value": value,
            "unit": unit,
            "metadata": metadata or {},
        }
        response = await self._request("POST", f"/devices/{device_id}/sensors/data", json=data)
        return response.json()




