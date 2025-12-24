"""Tests for job scraper."""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.job_scraper import BaseJobScraper
from app.services.job_api import IndeedScraper


@pytest.fixture
def scraper():
    """Create a test scraper."""
    return IndeedScraper()


@pytest.mark.asyncio
async def test_rate_limiting(scraper):
    """Test rate limiting."""
    import time
    
    start = time.time()
    await scraper.rate_limiter.wait()
    elapsed = time.time() - start
    
    # Should wait at least min_delay
    assert elapsed >= scraper.rate_limiter.min_delay - 0.1  # Allow small margin


@pytest.mark.asyncio
async def test_fetch_page_success(scraper):
    """Test successful page fetch."""
    with patch('app.services.job_scraper.BaseJobScraper.client.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response
        
        response = await scraper._fetch_page("http://example.com")
        
        assert response is not None
        assert response.text == "<html><body>Test</body></html>"


@pytest.mark.asyncio
async def test_fetch_page_retry(scraper):
    """Test retry logic on failure."""
    with patch('app.services.job_scraper.BaseJobScraper.client.get') as mock_get:
        # First call fails, second succeeds
        mock_get.side_effect = [
            Exception("Network error"),
            AsyncMock(text="<html>Success</html>", raise_for_status=AsyncMock())
        ]
        
        response = await scraper._fetch_page("http://example.com", retries=1)
        
        # Should retry and eventually succeed
        assert mock_get.call_count == 2


def test_parse_html(scraper):
    """Test HTML parsing."""
    html = "<html><body><h1>Test</h1></body></html>"
    soup = scraper._parse_html(html)
    
    assert soup.find("h1") is not None
    assert soup.find("h1").text == "Test"

