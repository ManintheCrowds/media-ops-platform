"""Shared helpers for official job-listing APIs.

Responses are treated as untrusted: types are checked, text is reduced to
escaped plain text, and URLs must be http(s) before a listing is kept.
"""

import asyncio
import html
import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_QUERY_SECRET_RE = re.compile(
    r"((?:api_key|app_key|app_id)=)[^&\s\"']+",
    re.IGNORECASE,
)


def _redact_secrets(value: str) -> str:
    return _QUERY_SECRET_RE.sub(r"\1REDACTED", value)


def _redact_arg(arg: object) -> object:
    """Redact secrets in strings and in objects whose text form contains them."""
    if isinstance(arg, str):
        return _redact_secrets(arg)
    text = str(arg)
    if "api_key=" in text or "app_key=" in text or "app_id=" in text:
        return _redact_secrets(text)
    return arg


class _SecretRedactFilter(logging.Filter):
    """Drop query-string credentials from HTTP client logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _redact_secrets(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(_redact_arg(arg) for arg in record.args)
        return True


def _install_secret_redact_filter() -> None:
    redact = _SecretRedactFilter()
    for name in ("httpx", "httpcore"):
        log = logging.getLogger(name)
        if not any(isinstance(item, _SecretRedactFilter) for item in log.filters):
            log.addFilter(redact)


_install_secret_redact_filter()

MAX_BACKOFF_SECONDS = 30
_UNSET_VALUES = frozenset(
    {
        "",
        "changeme",
        "your_key",
        "your-key",
        "your_api_key",
        "your-api-key",
        "your_api_key_here",
        "your-api-key-here",
        "none",
        "null",
        "todo",
    }
)
_TAG_RE = re.compile(r"<[^>]*>")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def credential_present(value: Optional[str]) -> bool:
    """Return whether a setting holds a real value rather than a placeholder."""
    if not isinstance(value, str):
        return False
    text = value.strip()
    lowered = text.lower()
    if not text or lowered in _UNSET_VALUES:
        return False
    if text.startswith("<") or lowered.startswith("your_") or lowered.startswith("your-"):
        return False
    return True


def email_present(value: Optional[str]) -> bool:
    """Return whether a value is a usable email and not a placeholder."""
    if not credential_present(value):
        return False
    return _EMAIL_RE.fullmatch(value.strip()) is not None


def display_text(value: object, max_len: int) -> str:
    """Strip markup and escape text so it is safe to show as HTML text."""
    if not isinstance(value, str):
        return ""
    text = _TAG_RE.sub(" ", value)
    text = html.unescape(text)
    text = _CONTROL_RE.sub("", text)
    text = " ".join(text.split())
    if max_len >= 0:
        text = text[:max_len]
    return html.escape(text, quote=True)


def safe_http_url(value: object, max_len: int = 2000) -> str:
    """Return an http(s) URL, or an empty string when the value is not one."""
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if not text or len(text) > max_len:
        return ""
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    if parsed.username or parsed.password:
        return ""
    return text


def dedupe_jobs(jobs: List[Dict]) -> List[Dict]:
    """Keep the first listing for each source and source id."""
    seen = set()
    kept: List[Dict] = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        source = job.get("source")
        source_id = job.get("source_id")
        if not isinstance(source, str) or not isinstance(source_id, str) or not source_id:
            continue
        key = (source, source_id)
        if key in seen:
            continue
        seen.add(key)
        kept.append(job)
    return kept


def positive_int(value: object, default: int) -> int:
    """Parse a positive integer from an untrusted API field."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            parsed = int(text)
            if parsed > 0:
                return parsed
    return default


def bounded_page_cap(value: object, default: int = 3, hard_cap: int = 20) -> int:
    """Clamp a configured page cap to a small positive range."""
    pages = positive_int(value, default)
    return min(pages, hard_cap)


def configure_official_interval(client) -> None:
    """Use a short fixed pause for official APIs instead of scraper delays."""
    interval = settings.official_api_min_interval_seconds
    if isinstance(interval, bool) or not isinstance(interval, (int, float)) or interval < 0:
        interval = 0.25
    client.rate_limiter.min_delay = float(interval)
    client.rate_limiter.max_delay = float(interval)
    client.rate_limiter.use_human_delays = False


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    """Honor Retry-After when it is a delay in seconds, and cap the wait."""
    raw = response.headers.get("Retry-After", "")
    if isinstance(raw, str) and raw.strip():
        try:
            seconds = float(raw.strip())
        except ValueError:
            seconds = -1
        if seconds >= 0:
            seconds = min(seconds, MAX_BACKOFF_SECONDS)
            if seconds.is_integer():
                return int(seconds)
            return seconds
    return min(MAX_BACKOFF_SECONDS, 2 ** attempt)


def _max_retries() -> int:
    retries = settings.max_retries
    if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
        return 0
    return min(retries, 5)


async def get_json(
    http: httpx.AsyncClient,
    rate_limiter,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, object]] = None,
    source_name: str,
) -> Optional[dict]:
    """GET JSON with a polite pause and capped backoff on HTTP 429.

    The request URL is not logged. Callers must keep secrets out of headers
    that this function would otherwise have no reason to record.
    """
    attempts = _max_retries() + 1
    for attempt in range(attempts):
        await rate_limiter.wait()
        try:
            response = await http.get(url, headers=headers, params=params)
        except httpx.TimeoutException:
            logger.error("%s API request timed out", source_name)
            return None
        except httpx.HTTPError as exc:
            logger.error("%s API request failed: %s", source_name, type(exc).__name__)
            return None

        if response.status_code == 429:
            if attempt >= attempts - 1:
                logger.warning(
                    "%s API returned HTTP 429; giving up after %s attempts",
                    source_name,
                    attempts,
                )
                return None
            delay = _retry_delay(response, attempt)
            logger.warning(
                "%s API returned HTTP 429; backing off %s seconds",
                source_name,
                delay,
            )
            await asyncio.sleep(delay)
            continue

        if response.status_code >= 400:
            logger.error("%s API returned HTTP %s", source_name, response.status_code)
            return None

        try:
            data = response.json()
        except ValueError:
            logger.error("%s API response was not JSON", source_name)
            return None
        if not isinstance(data, dict):
            logger.error("%s API response JSON was not an object", source_name)
            return None
        return data
    return None
