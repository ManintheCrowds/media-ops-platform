"""Tests for API client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pi_client.client import PiAPIClient
from pi_client.config import Config


@pytest.fixture
def config():
    """Create test configuration."""
    config = Config()
    config.device.device_id = "test-device"
    config.api.base_url = "https://test.example.com"
    config.api.auth_token = "test-token"
    return config


@pytest.mark.asyncio
async def test_get_content_list(config):
    """Test getting content list."""
    with patch('pi_client.client.httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1, "title": "Test"}]
        mock_response.raise_for_status = MagicMock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.request.return_value = mock_response
        mock_client_instance.__aenter__.return_value = mock_client_instance
        
        async with PiAPIClient(config) as client:
            client._client = mock_client_instance
            result = await client.get_content_list()
        
        assert len(result) == 1
        assert result[0]["id"] == 1


@pytest.mark.asyncio
async def test_stream_media(config):
    """Test streaming media."""
    with patch('pi_client.client.httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.content = b"test video data"
        mock_response.raise_for_status = MagicMock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.request.return_value = mock_response
        mock_client_instance.__aenter__.return_value = mock_client_instance
        
        async with PiAPIClient(config) as client:
            client._client = mock_client_instance
            response = await client.stream_media(1, start_byte=0, end_byte=1023)
        
        assert response.content == b"test video data"







