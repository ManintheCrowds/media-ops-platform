"""Have I Been Pwned (HIBP) Pwned Passwords API client (free)."""

import httpx
import asyncio
import hashlib
from datetime import datetime, timezone
from typing import Optional
import logging

from ..config import config

logger = logging.getLogger(__name__)


class HIBPClient:
    """Client for HIBP Pwned Passwords API (free, no API key required)."""
    
    USER_AGENT = "Security-Service/1.0"
    
    def __init__(self):
        self.rate_limit_delay = config.hibp_rate_limit_delay
        self.last_request_time = None
        
    async def _rate_limit_delay(self):
        """Enforce rate limiting between requests."""
        if self.last_request_time:
            elapsed = (datetime.now(timezone.utc) - self.last_request_time).total_seconds()
            if elapsed < self.rate_limit_delay:
                wait_time = self.rate_limit_delay - elapsed
                await asyncio.sleep(wait_time)
        self.last_request_time = datetime.now(timezone.utc)
    
    def hash_password(self, password: str) -> str:
        """
        Generate SHA-1 hash of password (for Pwned Passwords API).
        
        Args:
            password: Plain text password
        
        Returns:
            Uppercase SHA-1 hash
        """
        return hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    
    async def check_password(
        self,
        password: str,
        retries: int = 3
    ) -> int:
        """
        Check if password has been pwned using free Pwned Passwords API.
        
        Args:
            password: Plain text password to check
            retries: Number of retry attempts
        
        Returns:
            Number of times password appears in breach database (0 if not found)
        """
        password_hash = self.hash_password(password)
        hash_prefix = password_hash[:5]
        hash_suffix = password_hash[5:]
        
        # Use Pwned Passwords API (no auth required, free)
        url = f"https://api.pwnedpasswords.com/range/{hash_prefix}"
        
        for attempt in range(retries):
            try:
                await self._rate_limit_delay()
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, headers={"user-agent": self.USER_AGENT})
                    
                    if response.status_code == 200:
                        # Parse response
                        for line in response.text.strip().split('\n'):
                            if ':' in line:
                                suffix, count = line.split(':', 1)
                                if suffix.upper() == hash_suffix:
                                    return int(count)
                        return 0
                    elif response.status_code == 429:
                        # Rate limit exceeded - exponential backoff
                        retry_after = int(response.headers.get("retry-after", 2))
                        if attempt < retries - 1:
                            wait_time = retry_after * (2 ** attempt)
                            logger.warning(f"Pwned Passwords rate limit exceeded, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error("Pwned Passwords rate limit exceeded after retries")
                            return 0
                    else:
                        logger.error(f"Pwned Passwords API error: {response.status_code}")
                        return 0
            except httpx.TimeoutException:
                if attempt < retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Pwned Passwords request timeout, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Pwned Passwords request timeout after retries")
                    return 0
            except Exception as e:
                logger.error(f"Password check failed: {e}")
                return 0
        
        return 0

