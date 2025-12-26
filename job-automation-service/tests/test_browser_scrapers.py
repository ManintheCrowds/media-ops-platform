"""Tests for browser-based job scrapers."""

import pytest
import asyncio
from app.services.browser_scraper import BrowserJobScraper
from app.services.job_api import (
    IndeedScraper,
    LinkedInScraper,
    GlassdoorScraper,
    ZipRecruiterScraper
)


@pytest.fixture
def browser_scraper():
    """Create a test browser scraper."""
    return BrowserJobScraper("indeed")


@pytest.mark.asyncio
async def test_browser_scraper_initialization(browser_scraper):
    """Test browser scraper initializes correctly."""
    assert browser_scraper.source_name == "indeed"
    assert browser_scraper.browser is None  # Not initialized until first use
    assert browser_scraper.rate_limiter is not None


@pytest.mark.asyncio
async def test_browser_scraper_fetch_page_simple(browser_scraper):
    """Test browser scraper can fetch a simple page."""
    try:
        # Test with a simple, non-blocked site first
        html = await browser_scraper._fetch_page("https://httpbin.org/html", wait_timeout=10000)
        
        assert html is not None
        assert len(html) > 0
        assert "html" in html.lower() or "body" in html.lower()
    finally:
        await browser_scraper.close()


@pytest.mark.asyncio
@pytest.mark.xfail(reason="Indeed may block browser scrapers - test to verify")
async def test_browser_scraper_indeed_fetch():
    """Test browser scraper can fetch Indeed page."""
    scraper = BrowserJobScraper("indeed")
    try:
        url = "https://www.indeed.com/jobs?q=Python+developer&l=Minneapolis%2C+MN"
        html = await scraper._fetch_page(url, wait_timeout=30000)
        
        if html:
            assert len(html) > 0
            # Check for job-related content
            html_lower = html.lower()
            has_job_content = any(indicator in html_lower for indicator in ["job", "position", "career"])
            assert has_job_content, "Page should contain job-related content"
        else:
            pytest.skip("Browser scraper returned no HTML - may be blocked")
    finally:
        await scraper.close()


@pytest.mark.asyncio
@pytest.mark.xfail(reason="LinkedIn may block browser scrapers - test to verify")
async def test_browser_scraper_linkedin_fetch():
    """Test browser scraper can fetch LinkedIn page."""
    scraper = BrowserJobScraper("linkedin")
    try:
        url = "https://www.linkedin.com/jobs/search?keywords=Python%20developer"
        html = await scraper._fetch_page(url, wait_timeout=30000)
        
        if html:
            assert len(html) > 0
        else:
            pytest.skip("Browser scraper returned no HTML - may be blocked")
    finally:
        await scraper.close()


@pytest.mark.asyncio
@pytest.mark.xfail(reason="Glassdoor may block browser scrapers - test to verify")
async def test_browser_scraper_glassdoor_fetch():
    """Test browser scraper can fetch Glassdoor page."""
    scraper = BrowserJobScraper("glassdoor")
    try:
        url = "https://www.glassdoor.com/Job/jobs.htm?sc.keyword=Python+developer"
        html = await scraper._fetch_page(url, wait_timeout=30000)
        
        if html:
            assert len(html) > 0
        else:
            pytest.skip("Browser scraper returned no HTML - may be blocked")
    finally:
        await scraper.close()


@pytest.mark.asyncio
@pytest.mark.xfail(reason="ZipRecruiter may block browser scrapers - test to verify")
async def test_browser_scraper_ziprecruiter_fetch():
    """Test browser scraper can fetch ZipRecruiter page."""
    scraper = BrowserJobScraper("ziprecruiter")
    try:
        url = "https://www.ziprecruiter.com/jobs/search?search=Python+developer"
        html = await scraper._fetch_page(url, wait_timeout=30000)
        
        if html:
            assert len(html) > 0
        else:
            pytest.skip("Browser scraper returned no HTML - may be blocked")
    finally:
        await scraper.close()


@pytest.mark.asyncio
async def test_browser_scraper_human_behavior_simulation(browser_scraper):
    """Test human behavior simulation doesn't error."""
    try:
        await browser_scraper._init_browser()
        
        # Navigate to a simple page
        await browser_scraper.page.goto("https://httpbin.org/html", wait_until="networkidle", timeout=10000)
        
        # Test human behavior simulation
        await browser_scraper._simulate_human_behavior()
        
        # Should complete without errors
        assert browser_scraper.page is not None
    finally:
        await browser_scraper.close()


@pytest.mark.asyncio
async def test_browser_scraper_stealth_mode(browser_scraper):
    """Test that stealth mode scripts are injected."""
    try:
        await browser_scraper._init_browser()
        
        # Navigate to a page that checks for webdriver
        await browser_scraper.page.goto("https://httpbin.org/html", wait_until="networkidle", timeout=10000)
        
        # Check that webdriver property is hidden
        webdriver_value = await browser_scraper.page.evaluate("navigator.webdriver")
        assert webdriver_value is None or webdriver_value is False, "webdriver should be hidden"
        
        # Check that chrome object exists
        chrome_exists = await browser_scraper.page.evaluate("typeof window.chrome !== 'undefined'")
        assert chrome_exists, "Chrome object should exist"
    finally:
        await browser_scraper.close()


@pytest.mark.asyncio
async def test_browser_scraper_with_http_scraper_search():
    """Test browser scraper integrated with HTTP scraper search logic."""
    from app.services.job_source_manager import JobSourceManager
    
    manager = JobSourceManager()
    
    try:
        # Test with Indeed (most likely to work)
        jobs = await manager.search_via_browser(
            "indeed",
            "Python developer",
            "Minneapolis, MN",
            limit=3
        )
        
        # Should return a list (may be empty if blocked)
        assert isinstance(jobs, list)
        
        if len(jobs) > 0:
            # Verify job structure
            job = jobs[0]
            assert "title" in job or "url" in job
    finally:
        await manager.close()

