"""Browser-based job scraper using Playwright for JavaScript execution."""

import asyncio
import random
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from app.config import settings
from app.services.job_scraper import BaseJobScraper, USER_AGENTS
from app.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class BrowserJobScraper(BaseJobScraper):
    """Browser-based scraper using Playwright for JavaScript-heavy sites."""
    
    def __init__(self, source_name: str):
        """Initialize browser scraper.
        
        Args:
            source_name: Name of the job source (e.g., 'indeed', 'linkedin')
        """
        super().__init__(source_name)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self._cookies = []
        self._last_url = None
    
    async def _init_browser(self):
        """Initialize browser and context."""
        if self.browser is None:
            self.playwright = await async_playwright().start()
            
            # Browser launch options with stealth settings
            launch_options = {
                "headless": settings.headless if hasattr(settings, 'headless') else True,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ]
            }
            
            # Use Chromium for better compatibility
            self.browser = await self.playwright.chromium.launch(**launch_options)
            
            # Create context with realistic viewport and user agent
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": random.choice(USER_AGENTS),
                "locale": "en-US",
                "timezone_id": "America/Chicago",
                "permissions": ["geolocation"],
                "geolocation": {"latitude": 44.9778, "longitude": -93.2650},  # Minneapolis
                "extra_http_headers": self._get_enhanced_headers(),
            }
            
            self.context = await self.browser.new_context(**context_options)
            
            # Add stealth scripts to avoid detection
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                window.chrome = {
                    runtime: {}
                };
            """)
            
            self.page = await self.context.new_page()
    
    def _get_enhanced_headers(self) -> Dict[str, str]:
        """Get enhanced headers for browser requests."""
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "DNT": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
    
    async def _fetch_page(
        self,
        url: str,
        retries: int = None,
        wait_for_selector: Optional[str] = None,
        wait_timeout: int = 30000,
        **kwargs
    ) -> Optional[str]:
        """Fetch a page using browser with JavaScript execution.
        
        Args:
            url: URL to fetch
            retries: Number of retries (defaults to config)
            wait_for_selector: CSS selector to wait for (optional)
            wait_timeout: Maximum wait time in milliseconds
            **kwargs: Additional arguments (ignored for browser)
        
        Returns:
            HTML content as string or None if failed
        """
        retries = retries or settings.max_retries
        
        await self._init_browser()
        
        for attempt in range(retries + 1):
            try:
                # Rate limiting
                await self.rate_limiter.wait()
                
                # Add referer if we have a previous URL
                if self._last_url and hasattr(settings, 'enable_referer_chain') and settings.enable_referer_chain:
                    await self.context.set_extra_http_headers({
                        **self._get_enhanced_headers(),
                        "Referer": self._last_url,
                    })
                
                # Navigate to URL
                response = await self.page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=wait_timeout
                )
                
                if not response:
                    raise Exception("No response from page")
                
                # Wait for specific selector if provided
                if wait_for_selector:
                    try:
                        await self.page.wait_for_selector(wait_for_selector, timeout=wait_timeout)
                    except Exception as e:
                        logger.warning(f"Selector {wait_for_selector} not found: {e}")
                
                # Additional wait for JavaScript execution
                await asyncio.sleep(random.uniform(1.0, 3.0))
                
                # Simulate human-like behavior
                if hasattr(settings, 'stealth_mode') and settings.stealth_mode:
                    await self._simulate_human_behavior()
                
                # Get page content
                html = await self.page.content()
                
                # Save cookies
                self._cookies = await self.context.cookies()
                self._last_url = url
                
                # Log success
                import json
                import time
                from pathlib import Path
                debug_log_path = Path("C:/Users/artin/software/.cursor/debug.log")
                try:
                    log_entry = {
                        "sessionId": "scraper-debug",
                        "runId": f"browser-fetch-{int(time.time())}",
                        "hypothesisId": "H1",
                        "location": f"browser_scraper.py:_fetch_page",
                        "message": f"Fetched page via browser: {self.source_name}",
                        "data": {
                            "url": url,
                            "status_code": response.status,
                            "response_size": len(html),
                            "source": self.source_name,
                            "method": "browser",
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    with open(debug_log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_entry) + "\n")
                except Exception:
                    pass
                
                return html
                
            except Exception as e:
                logger.error(f"Browser error fetching {url} (attempt {attempt + 1}/{retries + 1}): {e}")
                
                if attempt < retries:
                    wait_time = 2 ** attempt * 2
                    logger.warning(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Log error
                    import json
                    import time
                    from pathlib import Path
                    debug_log_path = Path("C:/Users/artin/software/.cursor/debug.log")
                    try:
                        log_entry = {
                            "sessionId": "scraper-debug",
                            "runId": f"browser-fetch-{int(time.time())}",
                            "hypothesisId": "H2",
                            "location": f"browser_scraper.py:_fetch_page",
                            "message": f"Browser error: {self.source_name}",
                            "data": {
                                "url": url,
                                "error": str(e),
                                "error_type": type(e).__name__,
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
                    
                    return None
        
        return None
    
    async def _simulate_human_behavior(self):
        """Simulate human-like behavior to avoid detection."""
        # Random mouse movements
        viewport = self.page.viewport_size
        if viewport:
            for _ in range(random.randint(1, 3)):
                x = random.randint(0, viewport['width'])
                y = random.randint(0, viewport['height'])
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Random scroll
        scroll_amount = random.randint(100, 500)
        await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        await asyncio.sleep(random.uniform(0.5, 1.5))
    
    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML with BeautifulSoup.
        
        Args:
            html: HTML content
        
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, "lxml")
    
    async def close(self):
        """Close browser and cleanup."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        # Also close HTTP client
        await super().close()
    
    def __del__(self):
        """Cleanup on deletion."""
        # Note: This won't work for async cleanup, but helps with warnings
        pass

