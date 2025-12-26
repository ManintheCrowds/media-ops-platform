"""Fetcher for Pwdb-Public breach database via GitHub API."""

import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote
from datetime import datetime
from .fetcher_base import BaseFetcher

logger = logging.getLogger(__name__)


class PwdbPublicFetcher(BaseFetcher):
    """Fetches breach data from Pwdb-Public GitHub repository."""
    
    GITHUB_API_BASE = "https://api.github.com"
    PWDB_REPO_OWNER = "ignis-sec"
    PWDB_REPO_NAME = "Pwdb-Public"
    
    @property
    def source_name(self) -> str:
        """Return the name of this data source."""
        return "pwdb"
    
    def __init__(self, github_token: Optional[str] = None, rate_limit_delay: float = 1.0):
        """
        Initialize Pwdb-Public fetcher.
        
        Args:
            github_token: Optional GitHub token for higher rate limits
            rate_limit_delay: Delay between requests (default 1s)
        """
        super().__init__(rate_limit_delay=rate_limit_delay)
        self.github_token = github_token
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.username_pattern = re.compile(r'\b[a-zA-Z0-9_]{3,20}\b')
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for GitHub API requests."""
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        headers["Accept"] = "application/vnd.github.v3+json"
        return headers
    
    async def _search_github_repo(self, query: str, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search Pwdb-Public repository for identifier using GitHub API.
        
        Args:
            query: Search query (identifier)
            file_type: Optional file extension filter (e.g., 'txt', 'json')
        
        Returns:
            List of search results
        """
        breaches = []
        
        try:
            # Construct search query for GitHub API
            # Search in the specific repository
            repo_query = f'repo:{self.PWDB_REPO_OWNER}/{self.PWDB_REPO_NAME}'
            search_query = f'{repo_query} "{query}"'
            
            if file_type:
                search_query += f' extension:{file_type}'
            
            params = {"q": search_query}
            url = f"{self.GITHUB_API_BASE}/search/code?{urlencode(params)}"
            
            result = await self._make_request(url, headers=self._get_headers(), timeout=30.0)
            
            if result and isinstance(result, dict) and "items" in result:
                items = result["items"]
                logger.debug(f"Found {len(items)} potential matches in Pwdb-Public")
                
                for item in items:
                    # Extract file information
                    file_path = item.get("path", "")
                    file_url = item.get("html_url", "")
                    
                    # Try to get file content
                    content_url = item.get("url", "")
                    if content_url:
                        file_content = await self._get_file_content(content_url)
                        if file_content and query.lower() in file_content.lower():
                            # Create breach record
                            breach = {
                                "Name": f"Pwdb-Public: {file_path}",
                                "BreachDate": None,  # Pwdb doesn't provide dates per file
                                "DataClasses": ["Email addresses", "Usernames", "Passwords"],
                                "Description": f"Found in Pwdb-Public database file: {file_path}",
                                "PwnCount": None,
                                "IsVerified": True,
                                "Domain": None,
                                "_source": self.source_name,
                                "_file_path": file_path,
                                "_file_url": file_url
                            }
                            breaches.append(breach)
            
        except Exception as e:
            logger.error(f"Error searching Pwdb-Public repository: {e}")
        
        return breaches
    
    async def _get_file_content(self, content_url: str) -> Optional[str]:
        """
        Get file content from GitHub API.
        
        Args:
            content_url: GitHub API URL for file content
        
        Returns:
            File content as string or None
        """
        try:
            result = await self._make_request(content_url, headers=self._get_headers(), timeout=30.0)
            if result and isinstance(result, dict):
                # GitHub API returns base64 encoded content
                import base64
                content = result.get("content", "")
                if content:
                    # Remove newlines from base64 string
                    content = content.replace("\n", "")
                    try:
                        decoded = base64.b64decode(content).decode('utf-8', errors='ignore')
                        return decoded
                    except Exception as e:
                        logger.debug(f"Error decoding file content: {e}")
            return None
        except Exception as e:
            logger.debug(f"Error getting file content: {e}")
            return None
    
    async def check_email(self, email: str) -> List[Dict[str, Any]]:
        """
        Check if email appears in Pwdb-Public database.
        
        Args:
            email: Email address to check
        
        Returns:
            List of breach dictionaries or empty list
        """
        email_lower = email.lower()
        breaches = []
        
        try:
            # Search for email in repository
            results = await self._search_github_repo(email_lower)
            breaches.extend(results)
            
            # Also try searching in common file types
            for file_type in ['txt', 'json', 'csv']:
                type_results = await self._search_github_repo(email_lower, file_type=file_type)
                breaches.extend(type_results)
            
            # Deduplicate by file path
            seen_paths = set()
            unique_breaches = []
            for breach in breaches:
                file_path = breach.get("_file_path", "")
                if file_path and file_path not in seen_paths:
                    seen_paths.add(file_path)
                    unique_breaches.append(breach)
            
            if unique_breaches:
                logger.info(f"Found {len(unique_breaches)} Pwdb-Public matches for {email}")
            
        except Exception as e:
            logger.error(f"Error checking email in Pwdb-Public: {e}")
        
        return unique_breaches if 'unique_breaches' in locals() else breaches
    
    async def check_username(self, username: str) -> List[Dict[str, Any]]:
        """
        Check if username appears in Pwdb-Public database.
        
        Args:
            username: Username to check
        
        Returns:
            List of breach dictionaries or empty list
        """
        username_lower = username.lower()
        breaches = []
        
        try:
            # Search for username in repository
            results = await self._search_github_repo(username_lower)
            breaches.extend(results)
            
            # Also try searching in common file types
            for file_type in ['txt', 'json', 'csv']:
                type_results = await self._search_github_repo(username_lower, file_type=file_type)
                breaches.extend(type_results)
            
            # Deduplicate by file path
            seen_paths = set()
            unique_breaches = []
            for breach in breaches:
                file_path = breach.get("_file_path", "")
                if file_path and file_path not in seen_paths:
                    seen_paths.add(file_path)
                    unique_breaches.append(breach)
            
            if unique_breaches:
                logger.info(f"Found {len(unique_breaches)} Pwdb-Public matches for {username}")
            
        except Exception as e:
            logger.error(f"Error checking username in Pwdb-Public: {e}")
        
        return unique_breaches if 'unique_breaches' in locals() else breaches

