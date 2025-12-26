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
            
            # Randomize viewport for better fingerprint diversity
            viewport_widths = [1920, 1366, 1536, 1440, 1280]
            viewport_heights = [1080, 768, 864, 900, 720]
            viewport = {
                "width": random.choice(viewport_widths),
                "height": random.choice(viewport_heights)
            }
            
            # Create context with realistic viewport and user agent
            context_options = {
                "viewport": viewport,
                "user_agent": random.choice(USER_AGENTS),
                "locale": "en-US",
                "timezone_id": "America/Chicago",
                "permissions": ["geolocation"],
                "geolocation": {"latitude": 44.9778, "longitude": -93.2650},  # Minneapolis
                "extra_http_headers": self._get_enhanced_headers(),
                "color_scheme": "light",
            }
            
            self.context = await self.browser.new_context(**context_options)
            
            # Enhanced stealth scripts to avoid detection
            await self.context.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => {
                        const plugins = [];
                        for (let i = 0; i < 5; i++) {
                            plugins.push({
                                0: {type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format'},
                                description: 'Portable Document Format',
                                filename: 'internal-pdf-viewer',
                                length: 1,
                                name: 'Chrome PDF Plugin'
                            });
                        }
                        return plugins;
                    }
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                // Add Chrome runtime object
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Mask WebGL fingerprint
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter.call(this, parameter);
                };
                
                // Randomize canvas fingerprint
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function() {
                    const context = this.getContext('2d');
                    if (context) {
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            imageData.data[i] += Math.floor(Math.random() * 10) - 5;
                        }
                        context.putImageData(imageData, 0, 0);
                    }
                    return originalToDataURL.apply(this, arguments);
                };
                
                // Override battery API
                if (navigator.getBattery) {
                    navigator.getBattery = () => Promise.resolve({
                        charging: true,
                        chargingTime: 0,
                        dischargingTime: Infinity,
                        level: 1
                    });
                }
                
                // Override connection API
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        effectiveType: '4g',
                        rtt: 50,
                        downlink: 10,
                        saveData: false
                    })
                });
                
                // Override deviceMemory
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8
                });
                
                // Override hardwareConcurrency
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 4
                });
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
                debug_log_path = Path(settings.debug_log_path) if settings.debug_log_path else None
                if debug_log_path:
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
                    debug_log_path = Path(settings.debug_log_path) if settings.debug_log_path else None
                    if debug_log_path:
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
        viewport = self.page.viewport_size
        if not viewport:
            return
        
        # Random mouse movements with more realistic patterns
        num_movements = random.randint(2, 5)
        for i in range(num_movements):
            # Use Bezier-like curves for more natural movement
            start_x = random.randint(0, viewport['width'])
            start_y = random.randint(0, viewport['height'])
            end_x = random.randint(0, viewport['width'])
            end_y = random.randint(0, viewport['height'])
            
            # Move in steps to simulate smooth movement
            steps = random.randint(5, 15)
            for step in range(steps):
                t = step / steps
                # Simple linear interpolation (could be enhanced with Bezier)
                x = int(start_x + (end_x - start_x) * t)
                y = int(start_y + (end_y - start_y) * t)
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.01, 0.05))
            
            # Random pause between movements
            await asyncio.sleep(random.uniform(0.2, 0.8))
        
        # Realistic scrolling pattern (scroll down, pause, scroll more)
        scroll_pauses = random.randint(2, 4)
        total_scroll = 0
        for _ in range(scroll_pauses):
            scroll_amount = random.randint(200, 600)
            total_scroll += scroll_amount
            
            # Smooth scroll
            await self.page.evaluate(f"""
                window.scrollBy({{
                    top: {scroll_amount},
                    behavior: 'smooth'
                }});
            """)
            
            # Wait for scroll to complete
            await asyncio.sleep(random.uniform(0.8, 2.0))
            
            # Sometimes scroll back up a bit (human behavior)
            if random.random() < 0.3:
                back_scroll = random.randint(50, 150)
                await self.page.evaluate(f"window.scrollBy(0, -{back_scroll})")
                await asyncio.sleep(random.uniform(0.3, 0.7))
        
        # Random pause at end (reading time)
        await asyncio.sleep(random.uniform(1.0, 3.0))
    
    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML with BeautifulSoup.
        
        Args:
            html: HTML content
        
        Returns:
            BeautifulSoup object
        """
        # Try lxml first, fallback to html.parser (built-in)
        try:
            return BeautifulSoup(html, "lxml")
        except Exception:
            return BeautifulSoup(html, "html.parser")
    
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

