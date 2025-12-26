"""Tests for fetcher component."""

import pytest
from unittest.mock import AsyncMock, patch
from services.breach_monitor.fetcher import HIBPFetcher


@pytest.mark.asyncio
async def test_password_hashing():
    """Test password hashing."""
    fetcher = HIBPFetcher()
    hash_result = fetcher.hash_password("test123")
    
    assert len(hash_result) == 40  # SHA-1 hash length
    assert hash_result.isupper()
    assert hash_result == "7288EDD0FC3FFCBE93A0CF06E3568E28521687BC"


@pytest.mark.asyncio
async def test_check_email_with_api_key():
    """Test email checking with API key."""
    fetcher = HIBPFetcher(api_key="test-key")
    
    with patch('services.breach_monitor.fetcher.httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"Name": "TestBreach"}]
        mock_response.content = b'[{"Name": "TestBreach"}]'
        
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await fetcher.check_email("test@example.com")
        
        assert len(result) == 1
        assert result[0]["Name"] == "TestBreach"


@pytest.mark.asyncio
async def test_check_email_without_api_key():
    """Test email checking without API key returns empty."""
    fetcher = HIBPFetcher(api_key=None)
    result = await fetcher.check_email("test@example.com")
    assert result == []


@pytest.mark.asyncio
async def test_check_password():
    """Test password checking (free API)."""
    fetcher = HIBPFetcher()
    
    with patch('services.breach_monitor.fetcher.httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "7288EDD0FC3FFCBE93A0CF06E3568E28521687BC:100\n"
        
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await fetcher.check_password("test123")
        
        assert result == 100


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting between requests."""
    fetcher = HIBPFetcher()
    
    import asyncio
    from datetime import datetime, timezone
    
    start = datetime.now(timezone.utc)
    await fetcher._rate_limit_delay()
    await fetcher._rate_limit_delay()
    end = datetime.now(timezone.utc)
    
    elapsed = (end - start).total_seconds()
    # Should have at least 200ms delay
    assert elapsed >= 0.15  # Allow some tolerance


@pytest.mark.asyncio
async def test_source_name():
    """Test source name property."""
    fetcher = HIBPFetcher()
    assert fetcher.source_name == "hibp"

