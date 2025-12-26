"""Base fetcher class for all breach data sources."""

import asyncio
import logging
import httpx
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """Abstract base class for all breach data fetchers."""
    
    USER_AGENT = "HomeCyberRisk/1.0"
    DEFAULT_RATE_LIMIT_DELAY = 0.2  # 200ms default
    
    def __init__(self, rate_limit_delay: float = None):
        """
        Initialize base fetcher.
        
        Args:
            rate_limit_delay: Delay between requests in seconds
        """
        self.rate_limit_delay = rate_limit_delay or self.DEFAULT_RATE_LIMIT_DELAY
        self.last_request_time: Optional[datetime] = None
        # API health tracking
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_error: Optional[str] = None
        self.last_success_time: Optional[datetime] = None
        self.last_failure_time: Optional[datetime] = None
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of this data source."""
        pass
    
    async def _rate_limit_delay(self):
        """Enforce rate limiting between requests."""
        if self.last_request_time:
            elapsed = (datetime.now(timezone.utc) - self.last_request_time).total_seconds()
            if elapsed < self.rate_limit_delay:
                wait_time = self.rate_limit_delay - elapsed
                await asyncio.sleep(wait_time)
        self.last_request_time = datetime.now(timezone.utc)
    
    async def _make_request(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        retries: int = 3,
        timeout: float = 30.0
    ) -> Optional[Any]:
        """
        Make HTTP request with rate limiting and retry logic.
        
        Args:
            url: URL to request
            headers: Optional headers
            retries: Number of retry attempts
            timeout: Request timeout in seconds
        
        Returns:
            Response JSON, text, or None if failed
        """
        await self._rate_limit_delay()
        
        default_headers = {"user-agent": self.USER_AGENT}
        if headers:
            default_headers.update(headers)
        
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(url, headers=default_headers)
                    
                    if response.status_code == 200:
                        # Try JSON first, fall back to text
                        try:
                            result = response.json() if response.content else []
                        except Exception:
                            result = response.text if response.content else ""
                        # Track success
                        self.request_count += 1
                        self.success_count += 1
                        self.last_success_time = datetime.now(timezone.utc)
                        self.last_error = None
                        return result
                    elif response.status_code == 404:
                        # Not found is valid (no breaches)
                        self.request_count += 1
                        self.success_count += 1
                        self.last_success_time = datetime.now(timezone.utc)
                        self.last_error = None
                        return []
                    elif response.status_code == 429:
                        # Rate limit exceeded - exponential backoff
                        retry_after = int(response.headers.get("retry-after", 2))
                        if attempt < retries - 1:
                            wait_time = retry_after * (2 ** attempt)
                            logger.warning(f"[{self.source_name}] Rate limit exceeded, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            error_msg = f"Rate limit exceeded (429) after {retries} retries"
                            logger.error(f"[{self.source_name}] {error_msg}")
                            self.request_count += 1
                            self.failure_count += 1
                            self.last_failure_time = datetime.now(timezone.utc)
                            self.last_error = error_msg
                            return None
                    else:
                        error_msg = f"API error: {response.status_code} - {response.text[:200]}"
                        logger.error(f"[{self.source_name}] {error_msg}")
                        self.request_count += 1
                        self.failure_count += 1
                        self.last_failure_time = datetime.now(timezone.utc)
                        self.last_error = error_msg
                        return None
                        
            except httpx.TimeoutException:
                if attempt < retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"[{self.source_name}] Request timeout, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    error_msg = f"Request timeout after {retries} retries"
                    logger.error(f"[{self.source_name}] {error_msg}")
                    self.request_count += 1
                    self.failure_count += 1
                    self.last_failure_time = datetime.now(timezone.utc)
                    self.last_error = error_msg
                    return None
            except Exception as e:
                error_msg = f"Request failed: {str(e)}"
                logger.error(f"[{self.source_name}] {error_msg}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    self.request_count += 1
                    self.failure_count += 1
                    self.last_failure_time = datetime.now(timezone.utc)
                    self.last_error = error_msg
                    return None
        
        return None
    
    @abstractmethod
    async def check_email(self, email: str) -> List[Dict[str, Any]]:
        """
        Check if email has been breached.
        
        Args:
            email: Email address to check
        
        Returns:
            List of breach dictionaries or empty list
        """
        pass
    
    @abstractmethod
    async def check_username(self, username: str) -> List[Dict[str, Any]]:
        """
        Check if username has been breached.
        
        Args:
            username: Username to check
        
        Returns:
            List of breach dictionaries or empty list
        """
        pass
    
    async def check_domain(self, domain: str) -> List[Dict[str, Any]]:
        """
        Check if domain has been breached (optional, not all sources support).
        
        Args:
            domain: Domain to check
        
        Returns:
            List of breach dictionaries or empty list
        """
        # Default implementation returns empty
        # Override in subclasses that support domain checking
        return []
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get API health status for this fetcher.
        
        Returns:
            Dictionary with health metrics
        """
        success_rate = (self.success_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            "source": self.source_name,
            "request_count": self.request_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(success_rate, 2),
            "last_success": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_error": self.last_error,
            "is_healthy": self.failure_count < 3 or success_rate > 80  # Healthy if < 3 failures or > 80% success
        }
    
    async def check_health(self) -> bool:
        """
        Check if the API is currently available and healthy.
        
        Returns:
            True if API appears healthy, False otherwise
        """
        health = self.get_health_status()
        return health["is_healthy"]

