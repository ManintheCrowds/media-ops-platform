"""The Muse API v2 client.

The public jobs endpoint works without a key at 500 requests/hour. A real
THEMUSE_API_KEY or THE_MUSE_API_KEY raises that to 3,600 requests/hour.
The key is sent as the api_key query parameter and is never logged.
"""

import html
import logging
from typing import Dict, List, Optional

from app.config import settings
from app.services.api_clients.base_api_client import BaseAPIClient
from app.services.api_clients.official_api import (
    bounded_page_cap,
    configure_official_interval,
    credential_present,
    dedupe_jobs,
    display_text,
    get_json,
    positive_int,
    safe_http_url,
)

logger = logging.getLogger(__name__)

JOBS_URL = "https://www.themuse.com/api/public/jobs"
MUSE_CATEGORIES = {
    "accounting": "Accounting",
    "data science": "Data Science",
    "design": "Design",
    "education": "Education",
    "engineering": "Engineering",
    "finance": "Finance",
    "healthcare": "Healthcare",
    "human resources": "Human Resources",
    "legal": "Legal",
    "marketing": "Marketing",
    "operations": "Operations",
    "project management": "Project Management",
    "sales": "Sales",
    "software engineering": "Software Engineering",
    "writing": "Writing",
}


def resolved_muse_api_key() -> Optional[str]:
    """Return a configured Muse key, ignoring placeholders."""
    for candidate in (settings.themuse_api_key, settings.the_muse_api_key):
        if credential_present(candidate):
            return candidate.strip()
    return None


def _category_name(query: str) -> Optional[str]:
    return MUSE_CATEGORIES.get(query.strip().lower())


def _keywords(query: str, category: Optional[str]) -> List[str]:
    """Keywords used when the query is not a known Muse category."""
    if category:
        return []
    return [part.lower() for part in query.split() if len(part) >= 2]


def _matches(job: Dict, keywords: List[str]) -> bool:
    if not keywords:
        return True
    haystack = html.unescape(
        " ".join(
            str(job.get(field, ""))
            for field in ("title", "company", "location", "description")
        )
    ).lower()
    return all(word in haystack for word in keywords)


class TheMuseAPIClient(BaseAPIClient):
    """The Muse public jobs API client."""

    def __init__(self):
        """Initialize The Muse client. A missing key leaves the source enabled."""
        api_key = resolved_muse_api_key()
        timeout = settings.official_api_timeout_seconds
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            timeout = 20.0
        super().__init__("the_muse", api_key, timeout=float(timeout))
        configure_official_interval(self)
        if api_key:
            logger.info(
                "The Muse API key is set. Authenticated limit is 3600 requests/hour."
            )
        else:
            logger.info(
                "The Muse API key is unset (THEMUSE_API_KEY or THE_MUSE_API_KEY). "
                "Using the unauthenticated limit of 500 requests/hour. "
                "Set THEMUSE_API_KEY to raise the limit to 3600 requests/hour."
            )

    async def search_jobs(self, query: str, location: str, limit: int = 25) -> List[Dict]:
        """Search The Muse and normalize listings into the job model."""
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            return []
        query_text = query if isinstance(query, str) else ""
        location_text = location if isinstance(location, str) else ""
        category = _category_name(query_text)
        keywords = _keywords(query_text, category)
        max_pages = bounded_page_cap(settings.themuse_max_pages)
        jobs: List[Dict] = []
        seen = set()
        page = 1
        total_pages = None

        while page <= max_pages and len(jobs) < limit:
            params: Dict[str, object] = {"page": page, "descending": "true"}
            if category:
                params["category"] = category
            if location_text:
                params["location"] = location_text
            if self.api_key:
                params["api_key"] = self.api_key
            data = await get_json(
                self.client,
                self.rate_limiter,
                JOBS_URL,
                headers={"User-Agent": "media-ops-job-automation/0.1"},
                params=params,
                source_name="The Muse",
            )
            if not isinstance(data, dict):
                break
            if total_pages is None:
                total_pages = positive_int(data.get("page_count"), 1)
            results = data.get("results")
            if not isinstance(results, list) or not results:
                break
            for result in results:
                job = self._parse_result(result)
                if not job or job["source_id"] in seen or not _matches(job, keywords):
                    continue
                seen.add(job["source_id"])
                jobs.append(job)
                if len(jobs) >= limit:
                    break
            if page >= total_pages:
                break
            page += 1

        logger.info("The Muse API returned %s jobs", len(jobs))
        return dedupe_jobs(jobs)

    def _parse_result(self, result: object) -> Optional[Dict]:
        if not isinstance(result, dict):
            return None
        raw_id = result.get("id")
        if isinstance(raw_id, bool) or raw_id is None or isinstance(raw_id, (dict, list)):
            return None
        text_id = str(raw_id).strip()
        if not text_id.isalnum() or len(text_id) > 64:
            return None
        title = display_text(result.get("name"), 255)
        company_obj = result.get("company")
        company = ""
        if isinstance(company_obj, dict):
            company = display_text(company_obj.get("name"), 255)
        refs = result.get("refs") if isinstance(result.get("refs"), dict) else {}
        url = safe_http_url(refs.get("landing_page"))
        if not title or not company or not url:
            return None
        locations: List[str] = []
        raw_locations = result.get("locations")
        if isinstance(raw_locations, list):
            for loc in raw_locations:
                if isinstance(loc, dict):
                    name = display_text(loc.get("name"), 255)
                    if name:
                        locations.append(name)
        location = ", ".join(locations)[:255]
        remote = any(
            "remote" in name.lower() or "flexible" in name.lower() for name in locations
        )
        levels = result.get("levels")
        job_type = ""
        if isinstance(levels, list) and levels and isinstance(levels[0], dict):
            job_type = display_text(levels[0].get("name"), 50)
        posted = result.get("publication_date")
        contents = result.get("contents") if isinstance(result.get("contents"), str) else ""
        normalized = self._normalize_job_data(
            {
                "title": title,
                "company": company,
                "location": location,
                "description": display_text(contents, 20000),
                "url": url,
                "id": f"the_muse:{text_id}",
                "posted_date": posted if isinstance(posted, str) else "",
                "salary": "",
            }
        )
        normalized["salary_range"] = ""
        normalized["job_type"] = job_type
        normalized["remote"] = remote
        normalized["requirements"] = ""
        return normalized
