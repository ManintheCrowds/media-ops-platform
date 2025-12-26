"""Fetcher component for retrieving breach data from HIBP API."""

import logging
import hashlib
import httpx
from typing import List, Dict, Any, Optional
from .fetcher_base import BaseFetcher

logger = logging.getLogger(__name__)


class HIBPFetcher(BaseFetcher):
    """Fetches breach data from Have I Been Pwned API."""
    
    BASE_URL = "https://haveibeenpwned.com/api/v3"
    PWNED_PASSWORDS_URL = "https://api.pwnedpasswords.com/range"
    RATE_LIMIT_DELAY = 0.2  # 200ms between requests (HIBP requirement)
    
    @property
    def source_name(self) -> str:
        """Return the name of this data source."""
        return "hibp"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize HIBP fetcher.
        
        Args:
            api_key: Optional HIBP API key for paid features
        """
        super().__init__(rate_limit_delay=self.RATE_LIMIT_DELAY)
        self.api_key = api_key
    
    async def check_email(self, email: str) -> List[Dict[str, Any]]:
        """
        Check if email has been breached (requires API key).
        
        Args:
            email: Email address to check
        
        Returns:
            List of breach dictionaries or empty list
        """
        if not self.api_key:
            logger.debug("HIBP API key not provided, skipping email check")
            return []
        
        from urllib.parse import quote
        encoded_email = quote(email, safe='')
        url = f"{self.BASE_URL}/breachedaccount/{encoded_email}"
        headers = {"hibp-api-key": self.api_key}
        
        result = await self._make_request(url, headers=headers)
        
        if result is None:
            return []
        
        # Handle both list and single dict responses
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return [result]
        else:
            return []
    
    async def check_username(self, username: str) -> List[Dict[str, Any]]:
        """
        Check if username has been breached (requires API key).
        
        Args:
            username: Username to check
        
        Returns:
            List of breach dictionaries or empty list
        """
        if not self.api_key:
            logger.debug("HIBP API key not provided, skipping username check")
            return []
        
        from urllib.parse import quote
        encoded_username = quote(username, safe='')
        url = f"{self.BASE_URL}/breachedaccount/{encoded_username}"
        headers = {"hibp-api-key": self.api_key}
        
        result = await self._make_request(url, headers=headers)
        
        if result is None:
            return []
        
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return [result]
        else:
            return []
    
    async def check_domain(self, domain: str) -> List[Dict[str, Any]]:
        """
        Check if domain has been breached (requires API key).
        
        Args:
            domain: Domain to check
        
        Returns:
            List of breach dictionaries or empty list
        """
        if not self.api_key:
            logger.debug("HIBP API key not provided, skipping domain check")
            return []
        
        from urllib.parse import quote
        encoded_domain = quote(domain, safe='')
        url = f"{self.BASE_URL}/breacheddomain/{encoded_domain}"
        headers = {"hibp-api-key": self.api_key}
        
        result = await self._make_request(url, headers=headers)
        
        if result is None:
            return []
        
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return [result]
        else:
            return []
    
    def hash_password(self, password: str) -> str:
        """
        Generate SHA-1 hash of password (for Pwned Passwords API).
        
        Args:
            password: Plain text password
        
        Returns:
            Uppercase SHA-1 hash
        """
        return hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    
    async def check_password(self, password: str) -> int:
        """
        Check if password has been pwned (free API, no key required).
        
        Args:
            password: Plain text password to check
        
        Returns:
            Number of times password appears in breach database (0 if not found)
        """
        password_hash = self.hash_password(password)
        hash_prefix = password_hash[:5]
        hash_suffix = password_hash[5:]
        
        url = f"{self.PWNED_PASSWORDS_URL}/{hash_prefix}"
        
        try:
            await self._rate_limit_delay()
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers={"user-agent": self.USER_AGENT})
                
                if response.status_code == 200:
                    # Parse response (format: hash_suffix:count)
                    for line in response.text.strip().split('\n'):
                        if ':' in line:
                            suffix, count = line.split(':', 1)
                            if suffix.upper() == hash_suffix:
                                return int(count)
                    return 0
                else:
                    logger.error(f"Pwned Passwords API error: {response.status_code}")
                    return 0
        except Exception as e:
            logger.error(f"Password check failed: {e}")
            return 0

