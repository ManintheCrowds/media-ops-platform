"""Job source manager with fallback chain (API → Browser → HTTP)."""

import logging
from typing import List, Dict, Optional
from app.config import settings
from app.services.job_api import (
    IndeedScraper,
    LinkedInScraper,
    GlassdoorScraper,
    ZipRecruiterScraper,
)

# Optional browser scraper import (requires playwright)
try:
    from app.services.browser_scraper import BrowserJobScraper
    BROWSER_AVAILABLE = True
except ImportError:
    BrowserJobScraper = None
    BROWSER_AVAILABLE = False
from app.services.api_clients.adzuna_api import AdzunaAPIClient
from app.services.api_clients.the_muse_api import TheMuseAPIClient
from app.services.api_clients.jsearch_api import JSearchAPIClient

logger = logging.getLogger(__name__)


class JobSourceManager:
    """Manages multiple data sources with fallback chain."""
    
    def __init__(self):
        """Initialize job source manager."""
        self.use_browser_scraping = getattr(settings, 'use_browser_scraping', True)
        
        # Initialize API clients
        self.api_clients = {
            "adzuna": AdzunaAPIClient() if settings.adzuna_api_key and settings.adzuna_api_id else None,
            "the_muse": TheMuseAPIClient() if settings.the_muse_api_key else None,
            "jsearch": JSearchAPIClient() if settings.jsearch_api_key else None,
        }
        
        # Initialize HTTP scrapers
        self.http_scrapers = {
            "indeed": IndeedScraper(),
            "linkedin": LinkedInScraper(),
            "glassdoor": GlassdoorScraper(),
            "ziprecruiter": ZipRecruiterScraper(),
        }
        
        # Browser scrapers (created on demand)
        self.browser_scrapers = {}
    
    def _get_browser_scraper(self, source: str):
        """Get or create browser scraper for source.
        
        Args:
            source: Source name
        
        Returns:
            Browser scraper instance or None
        """
        if not BROWSER_AVAILABLE or BrowserJobScraper is None:
            return None
        
        if source not in self.browser_scrapers:
            # Create browser scraper based on source
            if source == "indeed":
                self.browser_scrapers[source] = BrowserJobScraper("indeed")
            elif source == "linkedin":
                self.browser_scrapers[source] = BrowserJobScraper("linkedin")
            elif source == "glassdoor":
                self.browser_scrapers[source] = BrowserJobScraper("glassdoor")
            elif source == "ziprecruiter":
                self.browser_scrapers[source] = BrowserJobScraper("ziprecruiter")
            else:
                return None
        
        return self.browser_scrapers.get(source)
    
    def has_api_client(self, source: str) -> bool:
        """Check if API client is available for source.
        
        Args:
            source: Source name
        
        Returns:
            True if API client is available
        """
        return source in self.api_clients and self.api_clients[source] is not None
    
    async def search_via_api(
        self,
        source: str,
        query: str,
        location: str,
        limit: int
    ) -> List[Dict]:
        """Search jobs via API client.
        
        Args:
            source: Source name
            query: Search query
            location: Location string
            limit: Maximum jobs to return
        
        Returns:
            List of job dictionaries
        """
        client = self.api_clients.get(source)
        if not client:
            return []
        
        try:
            return await client.search_jobs(query, location, limit)
        except Exception as e:
            logger.error(f"API search failed for {source}: {e}")
            return []
    
    async def search_via_browser(
        self,
        source: str,
        query: str,
        location: str,
        limit: int
    ) -> List[Dict]:
        """Search jobs via browser scraper.
        
        Args:
            source: Source name
            query: Search query
            location: Location string
            limit: Maximum jobs to return
        
        Returns:
            List of job dictionaries
        """
        browser_scraper = self._get_browser_scraper(source)
        if not browser_scraper:
            return []
        
        try:
            # Get the HTTP scraper to use its search logic
            http_scraper = self.http_scrapers.get(source)
            if not http_scraper:
                return []
            
            # Temporarily replace the HTTP scraper's _fetch_page with browser version
            # This allows us to use browser for fetching but HTTP scraper's parsing logic
            original_fetch = http_scraper._fetch_page
            
            async def browser_fetch(url, **kwargs):
                html = await browser_scraper._fetch_page(url, **kwargs)
                if html:
                    # Create a mock response object
                    class MockResponse:
                        def __init__(self, text):
                            self.text = text
                            self.status_code = 200
                            self.cookies = {}
                            self.headers = {}
                    return MockResponse(html)
                return None
            
            http_scraper._fetch_page = browser_fetch
            
            try:
                jobs = await http_scraper.search_jobs(query, location, limit)
            finally:
                # Restore original fetch method
                http_scraper._fetch_page = original_fetch
            
            return jobs
        except Exception as e:
            logger.error(f"Browser search failed for {source}: {e}")
            return []
    
    async def search_via_http(
        self,
        source: str,
        query: str,
        location: str,
        limit: int
    ) -> List[Dict]:
        """Search jobs via HTTP scraper.
        
        Args:
            source: Source name
            query: Search query
            location: Location string
            limit: Maximum jobs to return
        
        Returns:
            List of job dictionaries
        """
        scraper = self.http_scrapers.get(source)
        if not scraper:
            return []
        
        try:
            return await scraper.search_jobs(query, location, limit)
        except Exception as e:
            logger.error(f"HTTP search failed for {source}: {e}")
            return []
    
    async def search_jobs(
        self,
        query: str,
        location: str,
        sources: List[str],
        limit: int = 25
    ) -> List[Dict]:
        """Search jobs from multiple sources with fallback chain.
        
        Fallback order: API → Browser → HTTP
        
        Args:
            query: Search query
            location: Location string
            sources: List of source names
            limit: Maximum jobs per source
        
        Returns:
            List of job dictionaries from all sources
        """
        all_jobs = []
        
        for source in sources:
            jobs = []
            
            # Try API first
            if self.has_api_client(source):
                logger.info(f"Searching {source} via API")
                jobs = await self.search_via_api(source, query, location, limit)
            
            # Fallback to browser scraping
            if not jobs and self.use_browser_scraping:
                logger.info(f"Searching {source} via browser")
                jobs = await self.search_via_browser(source, query, location, limit)
            
            # Fallback to HTTP scraping
            if not jobs:
                logger.info(f"Searching {source} via HTTP")
                jobs = await self.search_via_http(source, query, location, limit)
            
            if jobs:
                logger.info(f"Found {len(jobs)} jobs from {source}")
                all_jobs.extend(jobs)
            else:
                logger.warning(f"No jobs found from {source}")
        
        return all_jobs
    
    async def close(self):
        """Close all clients and scrapers."""
        # Close API clients
        for client in self.api_clients.values():
            if client:
                await client.close()
        
        # Close browser scrapers
        for scraper in self.browser_scrapers.values():
            if scraper:
                await scraper.close()
        
        # Close HTTP scrapers
        for scraper in self.http_scrapers.values():
            if scraper:
                await scraper.close()

