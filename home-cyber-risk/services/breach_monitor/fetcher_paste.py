"""Fetcher for paste sites (Pastebin, GitHub Gists)."""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .fetcher_base import BaseFetcher

logger = logging.getLogger(__name__)


class PasteSiteFetcher(BaseFetcher):
    """Fetches breach data from paste sites."""
    
    # GitHub API rate limit: 60 requests/hour for unauthenticated
    GITHUB_API_BASE = "https://api.github.com"
    PASTEBIN_BASE = "https://pastebin.com"
    
    @property
    def source_name(self) -> str:
        """Return the name of this data source."""
        return "paste"
    
    def __init__(self, github_token: Optional[str] = None, rate_limit_delay: float = 60.0):
        """
        Initialize paste site fetcher.
        
        Args:
            github_token: Optional GitHub token for higher rate limits
            rate_limit_delay: Delay between requests (default 60s for GitHub API)
        """
        super().__init__(rate_limit_delay=rate_limit_delay)
        self.github_token = github_token
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.username_pattern = re.compile(r'\b[a-zA-Z0-9_]{3,20}\b')
    
    async def check_email(self, email: str) -> List[Dict[str, Any]]:
        """
        Check if email appears in paste sites.
        
        Args:
            email: Email address to check
        
        Returns:
            List of breach dictionaries or empty list
        """
        breaches = []
        
        # Check GitHub Gists
        gist_breaches = await self._check_github_gists(email, "email")
        breaches.extend(gist_breaches)
        
        # Note: Pastebin requires scraping which is more complex
        # For now, we'll focus on GitHub Gists which has a proper API
        
        return breaches
    
    async def check_username(self, username: str) -> List[Dict[str, Any]]:
        """
        Check if username appears in paste sites.
        
        Args:
            username: Username to check
        
        Returns:
            List of breach dictionaries or empty list
        """
        breaches = []
        
        # Check GitHub Gists
        gist_breaches = await self._check_github_gists(username, "username")
        breaches.extend(gist_breaches)
        
        return breaches
    
    async def _check_github_gists(self, identifier: str, identifier_type: str) -> List[Dict[str, Any]]:
        """
        Check GitHub Gists for identifier.
        
        Args:
            identifier: Email or username to search for
            identifier_type: Type of identifier
        
        Returns:
            List of breach dictionaries
        """
        breaches = []
        
        # GitHub code search API requires authentication
        if not self.github_token:
            logger.debug("GitHub token not provided, skipping paste site check (requires authentication)")
            return []
        
        try:
            # Search Gists (limited to public Gists)
            # Note: GitHub search API has rate limits
            from urllib.parse import urlencode
            search_query = f'"{identifier}" extension:txt OR extension:md'
            params = {"q": search_query}
            url = f"{self.GITHUB_API_BASE}/search/code?{urlencode(params)}"
            
            headers = {"Authorization": f"token {self.github_token}"}
            
            result = await self._make_request(url, headers=headers)
            
            if result and isinstance(result, dict) and "items" in result:
                for item in result.get("items", [])[:10]:  # Limit to 10 results
                    # Extract Gist info
                    gist_url = item.get("html_url", "")
                    if "gist.github.com" in gist_url:
                        breach = {
                            "Name": "GitHub Gist Leak",
                            "BreachDate": datetime.now().isoformat(),
                            "DataClasses": ["Email addresses", "Usernames"] if identifier_type == "email" else ["Usernames"],
                            "Description": f"Found in GitHub Gist: {gist_url}",
                            "PwnCount": None,
                            "IsVerified": False,
                            "Domain": None,
                            "_source": self.source_name,
                            "_identifier": identifier,
                            "_identifier_type": identifier_type,
                            "_gist_url": gist_url
                        }
                        breaches.append(breach)
            
        except Exception as e:
            logger.error(f"Error checking GitHub Gists: {e}")
        
        return breaches
    
    def _search_paste_content(self, content: str, identifier: str) -> bool:
        """
        Search for identifier in paste content.
        
        Args:
            content: Paste content to search
            identifier: Identifier to search for
        
        Returns:
            True if found, False otherwise
        """
        content_lower = content.lower()
        identifier_lower = identifier.lower()
        
        # Exact match
        if identifier_lower in content_lower:
            return True
        
        # Pattern matching for emails
        if "@" in identifier:
            if self.email_pattern.search(content):
                # Check if it's the same email
                emails = self.email_pattern.findall(content)
                if identifier_lower in [e.lower() for e in emails]:
                    return True
        
        return False


class PastebinFetcher(BaseFetcher):
    """
    Pastebin fetcher (requires scraping, more complex).
    Note: Pastebin has rate limits and may require authentication for API access.
    This is a placeholder for future implementation.
    """
    
    @property
    def source_name(self) -> str:
        """Return the name of this data source."""
        return "pastebin"
    
    async def check_email(self, email: str) -> List[Dict[str, Any]]:
        """Check Pastebin for email (not implemented yet)."""
        # Pastebin scraping is complex and may violate ToS
        # Consider using Pastebin API if available
        logger.debug("Pastebin checking not implemented")
        return []
    
    async def check_username(self, username: str) -> List[Dict[str, Any]]:
        """Check Pastebin for username (not implemented yet)."""
        logger.debug("Pastebin checking not implemented")
        return []

