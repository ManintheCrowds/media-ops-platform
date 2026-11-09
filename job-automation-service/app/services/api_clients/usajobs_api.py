"""USAJOBS Search API client.

Federal listings only. Both USAJOBS_API_KEY and USAJOBS_USER_AGENT_EMAIL must
be set to a non-placeholder value. The email is sent as User-Agent and is
never written to logs.
"""

import logging
import re
from typing import Dict, List, Optional

from app.config import settings
from app.services.api_clients.base_api_client import BaseAPIClient
from app.services.api_clients.official_api import (
    bounded_page_cap,
    configure_official_interval,
    credential_present,
    dedupe_jobs,
    display_text,
    email_present,
    get_json,
    positive_int,
    safe_http_url,
)

logger = logging.getLogger(__name__)

SEARCH_URL = "https://data.usajobs.gov/api/search"
_SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,80}$")


def missing_usajobs_env_names() -> List[str]:
    """Names of USAJOBS env vars that are unset or still placeholders."""
    missing: List[str] = []
    if not credential_present(settings.usajobs_api_key):
        missing.append("USAJOBS_API_KEY")
    if not email_present(settings.usajobs_user_agent_email):
        missing.append("USAJOBS_USER_AGENT_EMAIL")
    return missing


def usajobs_disabled_message(missing: Optional[List[str]] = None) -> str:
    """Name the env vars to set. Does not include their values."""
    names = missing_usajobs_env_names() if missing is None else missing
    listed = " and ".join(names) if names else "USAJOBS_API_KEY and USAJOBS_USER_AGENT_EMAIL"
    return (
        f"USAJOBS source is disabled. Set {listed} in the environment "
        "or an untracked .env file. Register at https://developer.usajobs.gov/. "
        "The user-agent value must be the email address registered with USAJOBS. "
        "Do not commit the key or the email."
    )


def usajobs_is_configured() -> bool:
    """Return whether both USAJOBS credentials are present."""
    return not missing_usajobs_env_names()


def _salary(value: object) -> str:
    if not isinstance(value, list) or not value or not isinstance(value[0], dict):
        return ""
    item = value[0]
    minimum = item.get("MinimumRange")
    maximum = item.get("MaximumRange")
    description = item.get("Description") if isinstance(item.get("Description"), str) else ""
    parts: List[str] = []
    has_min = minimum not in (None, "")
    has_max = maximum not in (None, "")
    if has_min and has_max:
        parts.append(f"{minimum}-{maximum}")
    elif has_min:
        parts.append(str(minimum))
    elif has_max:
        parts.append(str(maximum))
    if description.strip():
        parts.append(description.strip())
    return display_text(" ".join(parts), 100)


def _remote(descriptor: Dict) -> bool:
    flag = descriptor.get("RemoteIndicator")
    if isinstance(flag, bool):
        return flag
    if isinstance(flag, str) and flag.strip().lower() in {"true", "yes"}:
        return True
    location = descriptor.get("PositionLocationDisplay")
    return isinstance(location, str) and "remote" in location.lower()


def _details(descriptor: Dict) -> Dict:
    user_area = descriptor.get("UserArea")
    if isinstance(user_area, dict) and isinstance(user_area.get("Details"), dict):
        return user_area["Details"]
    return {}


class USAJobsAPIClient(BaseAPIClient):
    """USAJOBS Search API client."""

    def __init__(self):
        """Capture credentials now so later env changes do not leak into a live client."""
        api_key = settings.usajobs_api_key.strip() if credential_present(settings.usajobs_api_key) else None
        email = (
            settings.usajobs_user_agent_email.strip()
            if email_present(settings.usajobs_user_agent_email)
            else None
        )
        timeout = settings.official_api_timeout_seconds
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            timeout = 20.0
        super().__init__("usajobs", api_key, timeout=float(timeout))
        self.user_agent_email = email
        configure_official_interval(self)
        if not self.is_configured:
            logger.warning("%s", usajobs_disabled_message())

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.user_agent_email)

    async def search_jobs(self, query: str, location: str, limit: int = 25) -> List[Dict]:
        """Search federal listings and normalize them into the job model."""
        if not self.is_configured:
            logger.warning("%s", usajobs_disabled_message())
            return []
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            return []
        query_text = query if isinstance(query, str) else ""
        location_text = location if isinstance(location, str) else ""
        page_size = min(50, limit)
        max_pages = bounded_page_cap(settings.usajobs_max_pages)
        jobs: List[Dict] = []
        seen = set()
        page = 1
        total_pages = None

        while page <= max_pages and len(jobs) < limit:
            params: Dict[str, object] = {
                "Keyword": query_text,
                "ResultsPerPage": page_size,
                "Page": page,
                # Public announcements only. "All" and "Status" need extra authorization.
                "WhoMayApply": "public",
            }
            if location_text:
                params["LocationName"] = location_text
            data = await get_json(
                self.client,
                self.rate_limiter,
                SEARCH_URL,
                headers={
                    "Host": "data.usajobs.gov",
                    "User-Agent": self.user_agent_email,
                    "Authorization-Key": self.api_key,
                },
                params=params,
                source_name="USAJOBS",
            )
            if not isinstance(data, dict):
                break
            result = data.get("SearchResult")
            if not isinstance(result, dict):
                break
            if total_pages is None:
                user_area = result.get("UserArea")
                page_field = user_area.get("NumberOfPages") if isinstance(user_area, dict) else None
                total_pages = positive_int(page_field, 1)
            items = result.get("SearchResultItems")
            if not isinstance(items, list) or not items:
                break
            for item in items:
                job = self._parse_item(item)
                if not job or job["source_id"] in seen:
                    continue
                seen.add(job["source_id"])
                jobs.append(job)
                if len(jobs) >= limit:
                    break
            if page >= total_pages:
                break
            page += 1

        logger.info("USAJOBS API returned %s jobs", len(jobs))
        return dedupe_jobs(jobs)

    def _parse_item(self, item: object) -> Optional[Dict]:
        if not isinstance(item, dict):
            return None
        descriptor = item.get("MatchedObjectDescriptor")
        if not isinstance(descriptor, dict):
            return None
        object_id = item.get("MatchedObjectId")
        if isinstance(object_id, bool) or object_id is None or isinstance(object_id, (dict, list)):
            return None
        text_id = str(object_id).strip()
        if not _SOURCE_ID_RE.fullmatch(text_id):
            return None
        title = display_text(descriptor.get("PositionTitle"), 255)
        company = display_text(descriptor.get("OrganizationName"), 255) or display_text(
            descriptor.get("DepartmentName"), 255
        )
        url = safe_http_url(descriptor.get("PositionURI"))
        if not title or not company or not url:
            return None
        details = _details(descriptor)
        summary = details.get("JobSummary")
        if not isinstance(summary, str) or not summary.strip():
            summary = descriptor.get("QualificationSummary")
        requirements = details.get("Requirements")
        schedules = descriptor.get("PositionSchedule")
        job_type = ""
        if isinstance(schedules, list) and schedules and isinstance(schedules[0], dict):
            job_type = display_text(schedules[0].get("Name"), 50)
        posted = descriptor.get("PublicationStartDate")
        normalized = self._normalize_job_data(
            {
                "title": title,
                "company": company,
                "location": display_text(descriptor.get("PositionLocationDisplay"), 255),
                "description": display_text(summary, 20000),
                "url": url,
                "id": f"usajobs:{text_id}",
                "posted_date": posted if isinstance(posted, str) else "",
                "salary": _salary(descriptor.get("PositionRemuneration")),
            }
        )
        normalized["salary_range"] = normalized.get("salary", "")
        normalized["job_type"] = job_type
        normalized["remote"] = _remote(descriptor)
        normalized["requirements"] = display_text(requirements, 20000)
        return normalized
