"""Base API client for job search APIs."""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import httpx
from app.config import settings
from app.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class BaseAPIClient(ABC):
    """Base class for API clients."""
    
    def __init__(self, source_name: str, api_key: Optional[str] = None):
        """Initialize API client.
        
        Args:
            source_name: Name of the job source
            api_key: API key for authentication
        """
        self.source_name = source_name
        self.api_key = api_key
        self.rate_limiter = RateLimiter()
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
        )
    
    @abstractmethod
    async def search_jobs(
        self,
        query: str,
        location: str,
        limit: int = 25
    ) -> List[Dict]:
        """Search for jobs.
        
        Args:
            query: Search query/keywords
            location: Location string
            limit: Maximum number of jobs to return
        
        Returns:
            List of job dictionaries
        """
        pass
    
    def _normalize_job_data(self, job: Dict) -> Dict:
        """Normalize job data to standard format.
        
        Args:
            job: Raw job data from API
        
        Returns:
            Normalized job dictionary
        """
        return {
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "description": job.get("description", ""),
            "url": job.get("url", ""),
            "source": self.source_name,
            "source_id": job.get("id", ""),
            "posted_date": job.get("posted_date", ""),
            "salary": job.get("salary", ""),
        }
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def __del__(self):
        """Cleanup on deletion."""
        pass

