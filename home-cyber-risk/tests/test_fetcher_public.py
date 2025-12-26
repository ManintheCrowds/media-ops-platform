"""Tests for public breach fetcher."""

import pytest
from unittest.mock import patch, AsyncMock
from services.breach_monitor.fetcher_public import PublicBreachFetcher


@pytest.mark.asyncio
async def test_source_name():
    """Test source name property."""
    fetcher = PublicBreachFetcher()
    assert fetcher.source_name == "public_db"


@pytest.mark.asyncio
async def test_check_email_empty_cache():
    """Test email checking with empty cache."""
    fetcher = PublicBreachFetcher(cache_dir="test_cache")
    result = await fetcher.check_email("test@example.com")
    # Should return empty if cache is empty and no sources configured
    assert isinstance(result, list)


def test_extract_identifiers():
    """Test identifier extraction from breach record."""
    fetcher = PublicBreachFetcher()
    
    breach = {
        "email": "test@example.com",
        "username": "testuser"
    }
    
    identifiers = fetcher._extract_identifiers(breach)
    assert "test@example.com" in identifiers
    assert "testuser" in identifiers

