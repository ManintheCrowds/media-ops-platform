"""The Muse API client for job search."""

import logging
from typing import List, Dict, Optional
from urllib.parse import urlencode
import httpx
from app.config import settings
from app.services.api_clients.base_api_client import BaseAPIClient

logger = logging.getLogger(__name__)


class TheMuseAPIClient(BaseAPIClient):
    """The Muse API client."""
    
    BASE_URL = "https://www.themuse.com/api/public/jobs"
    
    def __init__(self):
        """Initialize The Muse API client."""
        api_key = settings.the_muse_api_key
        super().__init__("the_muse", api_key)
    
    async def search_jobs(
        self,
        query: str,
        location: str,
        limit: int = 25
    ) -> List[Dict]:
        """Search The Muse for jobs.
        
        Args:
            query: Job search query
            location: Location string
            limit: Maximum number of jobs to return
        
        Returns:
            List of job dictionaries
        """
        await self.rate_limiter.wait()
        
        # The Muse API uses different parameters
        params = {
            "page": 1,
            "descending": "true",
        }
        
        # Add query if provided
        if query:
            params["category"] = query  # The Muse uses categories
        
        # Add location if provided
        if location:
            params["location"] = location
        
        url = f"{self.BASE_URL}?{urlencode(params)}"
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            results = data.get("results", [])
            
            for result in results[:limit]:
                job = self._normalize_job_data({
                    "title": result.get("name", ""),
                    "company": result.get("company", {}).get("name", ""),
                    "location": ", ".join([loc.get("name", "") for loc in result.get("locations", [])]),
                    "description": result.get("contents", ""),
                    "url": result.get("refs", {}).get("landing_page", ""),
                    "id": str(result.get("id", "")),
                    "posted_date": result.get("publication_date", ""),
                    "salary": "",  # The Muse doesn't always provide salary
                })
                jobs.append(job)
            
            logger.info(f"The Muse API returned {len(jobs)} jobs")
            return jobs
            
        except httpx.HTTPStatusError as e:
            logger.error(f"The Muse API HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"The Muse API error: {e}")
            return []

