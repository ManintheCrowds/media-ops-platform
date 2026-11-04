"""Adzuna API client for job search."""

import logging
from typing import List, Dict, Optional
from urllib.parse import urlencode
import httpx
from app.config import settings
from app.services.api_clients.base_api_client import BaseAPIClient

logger = logging.getLogger(__name__)

# Example files and docs use these stand-ins. They are not credentials.
_UNSET_VALUES = frozenset(
    {
        "",
        "changeme",
        "your_key",
        "your_id",
        "your-key",
        "your-id",
        "your_api_id",
        "your_api_key",
        "your-adzuna-api-id-here",
        "your-adzuna-api-key-here",
        "your_adzuna_api_id_here",
        "your_adzuna_api_key_here",
        "none",
        "null",
        "todo",
    }
)


class AdzunaCredentialsError(RuntimeError):
    """Raised when Adzuna is used without ADZUNA_API_ID and ADZUNA_API_KEY."""


def _credential_present(value: Optional[str]) -> bool:
    """Return whether a setting holds a real credential rather than a placeholder."""
    if value is None:
        return False
    text = value.strip()
    lowered = text.lower()
    if not text or lowered in _UNSET_VALUES:
        return False
    if (
        text.startswith("<")
        or lowered.startswith("your_")
        or lowered.startswith("your-")
    ):
        return False
    return True


def missing_adzuna_env_names() -> List[str]:
    """Names of Adzuna env vars that are unset or still placeholders.

    Values are read only from the process environment (or an untracked .env
    loaded by settings). This function never returns the values themselves.
    """
    missing: List[str] = []
    if not _credential_present(settings.adzuna_api_id):
        missing.append("ADZUNA_API_ID")
    if not _credential_present(settings.adzuna_api_key):
        missing.append("ADZUNA_API_KEY")
    return missing


def adzuna_credentials_message(missing: Optional[List[str]] = None) -> str:
    """Helpful error text naming the env vars to set. Does not include values."""
    names = missing_adzuna_env_names() if missing is None else missing
    listed = " and ".join(names) if names else "ADZUNA_API_ID and ADZUNA_API_KEY"
    return (
        f"Adzuna API credentials are missing ({listed}). "
        "Set both in the service environment or an untracked .env file. "
        "Issue them from the Adzuna developer account. Do not commit the values."
    )


class AdzunaAPIClient(BaseAPIClient):
    """Adzuna API client."""

    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(self):
        """Initialize Adzuna API client from environment-backed settings."""
        api_key = (
            settings.adzuna_api_key
            if _credential_present(settings.adzuna_api_key)
            else None
        )
        api_id = (
            settings.adzuna_api_id
            if _credential_present(settings.adzuna_api_id)
            else None
        )

        if not api_key or not api_id:
            logger.warning("%s", adzuna_credentials_message())

        super().__init__("adzuna", api_key)
        self.api_id = api_id
        self.country = "us"  # Default to US, can be configured

    async def search_jobs(
        self, query: str, location: str, limit: int = 25
    ) -> List[Dict]:
        """Search Adzuna for jobs.

        Args:
            query: Job search query
            location: Location string
            limit: Maximum number of jobs to return

        Returns:
            List of job dictionaries
        """
        missing = missing_adzuna_env_names()
        if missing:
            message = adzuna_credentials_message(missing)
            logger.error("%s", message)
            raise AdzunaCredentialsError(message)

        self.api_key = settings.adzuna_api_key
        self.api_id = settings.adzuna_api_id

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
                job = self._normalize_job_data(
                    {
                        "title": result.get("title", ""),
                        "company": result.get("company", {}).get("display_name", ""),
                        "location": result.get("location", {}).get("display_name", ""),
                        "description": result.get("description", ""),
                        "url": result.get("redirect_url", ""),
                        "id": result.get("id", ""),
                        "posted_date": result.get("created", ""),
                        "salary": (
                            result.get("salary_min", "")
                            if result.get("salary_min")
                            else ""
                        ),
                    }
                )
                jobs.append(job)

            logger.info(f"Adzuna API returned {len(jobs)} jobs")
            return jobs

        except httpx.HTTPStatusError as e:
            logger.error(f"Adzuna API HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Adzuna API error: {e}")
            return []
