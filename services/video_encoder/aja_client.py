"""AJA HELO REST API Client."""

from typing import Dict, Optional, Union
import aiohttp
import asyncio
from datetime import datetime
from enum import Enum
from app.exceptions import EncoderConnectionError, EncoderRecordingError


class AJAHELOEndpoints(Enum):
    """AJA HELO API endpoints."""
    # Control endpoints
    STREAM_START = "/control/stream/start"
    STREAM_STOP = "/control/stream/stop"
    RECORD_START = "/control/record/start"
    RECORD_STOP = "/control/record/stop"
    REBOOT = "/control/reboot"
    
    # Status endpoints
    SYSTEM_STATUS = "/status/system"
    STREAM_STATUS = "/status/streaming"
    RECORD_STATUS = "/status/recording"
    NETWORK_STATUS = "/status/network"
    MEDIA_STATUS = "/status/media"
    
    # Configuration endpoints
    STREAM_CONFIG = "/config/stream"
    RECORD_CONFIG = "/config/record"
    NETWORK_CONFIG = "/config/network"
    SYSTEM_CONFIG = "/config/system"


class AJAHELOClient:
    """AJA HELO REST API Client for recording and streaming."""
    
    def __init__(self, ip_address: str, port: int = 80, timeout: int = 30):
        """Initialize AJA HELO client."""
        self.base_url = f"http://{ip_address}:{port}/api/v1"
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
        self._last_error = None
        self._connection_retries = 3

    async def _handle_api_error(self, response: aiohttp.ClientResponse) -> None:
        """Handle API error responses."""
        try:
            error_data = await response.json()
            error_msg = error_data.get('error', 'Unknown error')
        except (ValueError, aiohttp.ContentTypeError, asyncio.TimeoutError) as e:
            # Response is not valid JSON, use status code as error message
            logger.debug(f"Could not parse error response as JSON: {e}")
            error_msg = f"HTTP {response.status}"
        
        if response.status == 400:
            raise EncoderRecordingError(f"Invalid request: {error_msg}")
        elif response.status == 401:
            raise EncoderConnectionError("Authentication required")
        elif response.status == 403:
            raise EncoderConnectionError("Operation not permitted")
        elif response.status == 404:
            raise EncoderConnectionError(f"Resource not found: {error_msg}")
        elif response.status == 409:
            raise EncoderRecordingError(f"Operation conflict: {error_msg}")
        else:
            raise EncoderConnectionError(f"API error ({response.status}): {error_msg}")

    async def _make_request(
        self,
        method: str,
        endpoint: Union[str, AJAHELOEndpoints],
        **kwargs
    ) -> Dict:
        """Make authenticated request with retries and error handling."""
        if isinstance(endpoint, AJAHELOEndpoints):
            endpoint = endpoint.value

        url = f"{self.base_url}{endpoint}"
        retries = self._connection_retries

        while retries > 0:
            try:
                if not self.session:
                    self.session = aiohttp.ClientSession(timeout=self.timeout)

                async with self.session.request(method, url, **kwargs) as response:
                    if response.status >= 400:
                        await self._handle_api_error(response)
                    return await response.json()

            except aiohttp.ClientConnectorError:
                retries -= 1
                if retries == 0:
                    raise EncoderConnectionError("Failed to connect to encoder")
                await asyncio.sleep(1)

            except aiohttp.ClientError as e:
                self._last_error = str(e)
                raise EncoderConnectionError(f"Connection error: {str(e)}")

    async def start_stream(self, config: Optional[Dict] = None) -> Dict:
        """Start streaming with optional configuration."""
        if config:
            await self.configure_stream(config)
        return await self._make_request("POST", AJAHELOEndpoints.STREAM_START)

    async def stop_stream(self) -> Dict:
        """Stop current stream."""
        return await self._make_request("POST", AJAHELOEndpoints.STREAM_STOP)

    async def start_recording(self, config: Optional[Dict] = None) -> Dict:
        """Start recording with optional configuration."""
        if config:
            await self.configure_recording(config)
        return await self._make_request("POST", AJAHELOEndpoints.RECORD_START)

    async def stop_recording(self) -> Dict:
        """Stop current recording."""
        return await self._make_request("POST", AJAHELOEndpoints.RECORD_STOP)

    async def reboot_device(self) -> Dict:
        """Reboot the HELO device."""
        return await self._make_request("POST", AJAHELOEndpoints.REBOOT)

    async def get_full_status(self) -> Dict:
        """Get comprehensive device status."""
        try:
            status_results = await asyncio.gather(
                self._make_request("GET", AJAHELOEndpoints.SYSTEM_STATUS),
                self._make_request("GET", AJAHELOEndpoints.STREAM_STATUS),
                self._make_request("GET", AJAHELOEndpoints.RECORD_STATUS),
                self._make_request("GET", AJAHELOEndpoints.NETWORK_STATUS),
                return_exceptions=True
            )

            return {
                'timestamp': datetime.utcnow().isoformat(),
                'system': status_results[0] if not isinstance(status_results[0], Exception) else None,
                'streaming': status_results[1] if not isinstance(status_results[1], Exception) else None,
                'recording': status_results[2] if not isinstance(status_results[2], Exception) else None,
                'network': status_results[3] if not isinstance(status_results[3], Exception) else None,
                'errors': [str(r) for r in status_results if isinstance(r, Exception)]
            }
        except Exception as e:
            raise EncoderConnectionError(f"Failed to get device status: {str(e)}")

    async def configure_stream(self, config: Dict) -> Dict:
        """Configure streaming parameters."""
        return await self._make_request("POST", AJAHELOEndpoints.STREAM_CONFIG, json=config)

    async def configure_recording(self, config: Dict) -> Dict:
        """Configure recording parameters."""
        return await self._make_request("POST", AJAHELOEndpoints.RECORD_CONFIG, json=config)

    async def get_network_stats(self) -> Dict:
        """Get network statistics."""
        return await self._make_request("GET", AJAHELOEndpoints.NETWORK_STATUS)

    async def get_media_status(self) -> Dict:
        """Get media and storage status."""
        return await self._make_request("GET", AJAHELOEndpoints.MEDIA_STATUS)

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

