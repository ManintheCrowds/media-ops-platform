"""Base job scraper with rate limiting and error handling."""

import asyncio
import random
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import httpx
from app.config import settings
from app.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


# User agent rotation list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Accept-Language variations
ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-US,en;q=0.9,es;q=0.8",
    "en-GB,en;q=0.9",
    "en-US,en;q=0.8",
]


class BaseJobScraper:
    """Base class for job scrapers with common functionality."""
    
    def __init__(self, source_name: str):
        """Initialize base scraper.
        
        Args:
            source_name: Name of the job source (e.g., 'indeed', 'linkedin')
        """
        self.source_name = source_name
        self.rate_limiter = RateLimiter()
        self._last_url = None
        self._cookies = {}
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=self._get_enhanced_headers()
        )
    
    def _get_enhanced_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """Get enhanced headers for HTTP requests.
        
        Args:
            referer: Referer URL if available
        
        Returns:
            Dictionary of headers
        """
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": random.choice(ACCEPT_LANGUAGES),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }
        
        # Add referer if enabled and available
        if referer and getattr(settings, 'enable_referer_chain', True):
            headers["Referer"] = referer
        
        # Add Sec-Fetch headers (modern browsers)
        if referer:
            headers["Sec-Fetch-Dest"] = "document"
            headers["Sec-Fetch-Mode"] = "navigate"
            headers["Sec-Fetch-Site"] = "same-origin" if self._is_same_origin(referer) else "cross-site"
            headers["Sec-Fetch-User"] = "?1"
        else:
            headers["Sec-Fetch-Dest"] = "document"
            headers["Sec-Fetch-Mode"] = "navigate"
            headers["Sec-Fetch-Site"] = "none"
            headers["Sec-Fetch-User"] = "?1"
        
        return headers
    
    def _is_same_origin(self, url: str) -> bool:
        """Check if URL is same origin as base.
        
        Args:
            url: URL to check
        
        Returns:
            True if same origin
        """
        # Simple check - can be enhanced
        return url.startswith("http") and any(domain in url for domain in [
            "indeed.com", "linkedin.com", "glassdoor.com", "ziprecruiter.com"
        ])
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent."""
        return random.choice(USER_AGENTS)
    
    async def _fetch_page(
        self,
        url: str,
        retries: int = None,
        **kwargs
    ) -> Optional[httpx.Response]:
        """Fetch a page with retry logic.
        
        Args:
            url: URL to fetch
            retries: Number of retries (defaults to config)
            **kwargs: Additional arguments for httpx request
        
        Returns:
            Response object or None if all retries failed
        """
        retries = retries or settings.max_retries
        
        for attempt in range(retries + 1):
            try:
                # Rate limiting
                await self.rate_limiter.wait()
                
                # Get enhanced headers with referer chain
                referer = self._last_url if getattr(settings, 'enable_referer_chain', True) else None
                enhanced_headers = self._get_enhanced_headers(referer=referer)
                
                # Merge with any provided headers
                headers = kwargs.get("headers", {})
                headers.update(enhanced_headers)
                kwargs["headers"] = headers
                
                # Add cookies if persistence is enabled
                if getattr(settings, 'cookie_persistence', True) and self._cookies:
                    kwargs["cookies"] = self._cookies
                
                # #region agent log
                import json
                import time
                from pathlib import Path
                debug_log_path = Path("C:/Users/artin/software/.cursor/debug.log")
                start_time = time.time()
                # #endregion agent log
                
                response = await self.client.get(url, **kwargs)
                response.raise_for_status()
                
                # Save cookies if persistence is enabled
                if getattr(settings, 'cookie_persistence', True):
                    for cookie in response.cookies.jar:
                        self._cookies[cookie.name] = cookie.value
                
                # Save last URL for referer chain
                self._last_url = url
                
                # #region agent log
                elapsed = time.time() - start_time
                try:
                    log_entry = {
                        "sessionId": "scraper-debug",
                        "runId": f"fetch-{int(time.time())}",
                        "hypothesisId": "H1",
                        "location": f"job_scraper.py:_fetch_page",
                        "message": f"Fetched page: {self.source_name}",
                        "data": {
                            "url": url,
                            "status_code": response.status_code,
                            "response_size": len(response.text),
                            "elapsed_time_ms": round(elapsed * 1000, 2),
                            "source": self.source_name,
                            "headers_present": bool(response.headers),
                            "content_type": response.headers.get("content-type", ""),
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    with open(debug_log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_entry) + "\n")
                except Exception:
                    pass
                # #endregion agent log
                
                return response
                
            except httpx.HTTPStatusError as e:
                # #region agent log
                import json
                import time
                from pathlib import Path
                debug_log_path = Path("C:/Users/artin/software/.cursor/debug.log")
                try:
                    log_entry = {
                        "sessionId": "scraper-debug",
                        "runId": f"fetch-{int(time.time())}",
                        "hypothesisId": "H2",
                        "location": f"job_scraper.py:_fetch_page",
                        "message": f"HTTP error: {self.source_name}",
                        "data": {
                            "url": url,
                            "status_code": e.response.status_code,
                            "error_type": "HTTPStatusError",
                            "source": self.source_name,
                            "attempt": attempt,
                            "retries_remaining": retries - attempt,
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    with open(debug_log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_entry) + "\n")
                except Exception:
                    pass
                # #endregion agent log
                
                if e.response.status_code == 429:  # Too Many Requests
                    wait_time = 2 ** attempt * 5  # Exponential backoff
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                    await asyncio.sleep(wait_time)
                elif e.response.status_code >= 500:
                    # Server error, retry
                    if attempt < retries:
                        wait_time = 2 ** attempt
                        logger.warning(f"Server error {e.response.status_code}, retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                else:
                    logger.error(f"HTTP error {e.response.status_code} for {url}")
                    return None
                    
            except httpx.RequestError as e:
                if attempt < retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request error: {e}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Request failed after {retries} retries: {e}")
                    return None
                    
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return None
        
        return None
    
    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML with BeautifulSoup.
        
        Args:
            html: HTML content
        
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, "lxml")
    
    async def search_jobs(
        self,
        query: str,
        location: str,
        limit: int = 25
    ) -> List[Dict]:
        """Search for jobs (to be implemented by subclasses).
        
        Args:
            query: Search query/keywords
            location: Location string
            limit: Maximum number of jobs to return
        
        Returns:
            List of job dictionaries
        """
        raise NotImplementedError("Subclasses must implement search_jobs")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def __del__(self):
        """Cleanup on deletion."""
        # Note: This won't work for async cleanup, but helps with warnings
        pass

