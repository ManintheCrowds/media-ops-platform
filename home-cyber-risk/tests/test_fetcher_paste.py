"""Tests for paste site fetcher."""

import pytest
from services.breach_monitor.fetcher_paste import PasteSiteFetcher


@pytest.mark.asyncio
async def test_source_name():
    """Test source name property."""
    fetcher = PasteSiteFetcher()
    assert fetcher.source_name == "paste"


@pytest.mark.asyncio
async def test_check_email():
    """Test email checking (may return empty if no API access)."""
    fetcher = PasteSiteFetcher()
    result = await fetcher.check_email("test@example.com")
    assert isinstance(result, list)


def test_search_paste_content():
    """Test searching paste content for identifier."""
    fetcher = PasteSiteFetcher()
    
    content = "Email: test@example.com\nPassword: secret123"
    
    assert fetcher._search_paste_content(content, "test@example.com") is True
    assert fetcher._search_paste_content(content, "nonexistent@example.com") is False

