"""Adzuna API client for job search."""

import logging
from typing import List, Dict, Optional
from urllib.parse import urlencode
import httpx
from app.config import settings
from app.services.api_clients.base_api_client import BaseAPIClient

logger = logging.getLogger(__name__)


class AdzunaAPIClient(BaseAPIClient):
    """Adzuna API client."""
    
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"
    
    def __init__(self):
        """Initialize Adzuna API client."""
        api_key = settings.adzuna_api_key
        api_id = settings.adzuna_api_id
        
        if not api_key or not api_id:
            logger.warning("Adzuna API key or ID not configured")
        
        super().__init__("adzuna", api_key)
        self.api_id = api_id
        self.country = "us"  # Default to US, can be configured
    
    async def search_jobs(
        self,
        query: str,
        location: str,
        limit: int = 25
    ) -> List[Dict]:
        """Search Adzuna for jobs.
        
        Args:
            query: Job search query
            location: Location string
            limit: Maximum number of jobs to return
        
        Returns:
            List of job dictionaries
        """
        if not self.api_key or not self.api_id:
            logger.error("Adzuna API credentials not configured")
            return []
        
        await self.rate_limiter.wait()
        
        # Parse location (simple - can be enhanced)
        location_parts = location.split(",")
        city = location_parts[0].strip() if location_parts else ""
        
        params = {
            "app_id": self.api_id,
            "app_key": self.api_key,
            "what": query,
            "where": city,
            "results_per_page": min(limit, 50),  # Adzuna max is 50
            "content-type": "application/json",
        }
        
        url = f"{self.BASE_URL}/{self.country}/search/1?{urlencode(params)}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            results = data.get("results", [])
            
            for result in results[:limit]:
                job = self._normalize_job_data({
                    "title": result.get("title", ""),
                    "company": result.get("company", {}).get("display_name", ""),
                    "location": result.get("location", {}).get("display_name", ""),
                    "description": result.get("description", ""),
                    "url": result.get("redirect_url", ""),
                    "id": result.get("id", ""),
                    "posted_date": result.get("created", ""),
                    "salary": result.get("salary_min", "") if result.get("salary_min") else "",
                })
                jobs.append(job)
            
            logger.info(f"Adzuna API returned {len(jobs)} jobs")
            return jobs
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Adzuna API HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Adzuna API error: {e}")
            return []

