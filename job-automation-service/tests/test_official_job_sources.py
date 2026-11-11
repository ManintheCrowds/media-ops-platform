"""Fixture tests for USAJOBS and The Muse. No live network."""

import json
import logging
from pathlib import Path

import httpx
import pytest
import respx

from app.api.jobs import SUPPORTED_SOURCES
from app.config import settings
from app.models.job_listing import JobListing
from app.schemas.job import JobSearchRequest
from app.services.api_clients.official_api import credential_present, dedupe_jobs
from app.services.api_clients.the_muse_api import TheMuseAPIClient
from app.services.api_clients.usajobs_api import USAJobsAPIClient
from app.services.job_source_manager import JobSourceManager
from app.services.scheduler import DEFAULT_SCHEDULE_SOURCES, run_scheduled_search

FIXTURES = Path(__file__).parent / "fixtures" / "official_apis"
USAJOBS_URL = "https://data.usajobs.gov/api/search"
MUSE_URL = "https://www.themuse.com/api/public/jobs"


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _silence_interval(monkeypatch):
    monkeypatch.setattr(settings, "official_api_min_interval_seconds", 0)
    monkeypatch.setattr(settings, "official_api_timeout_seconds", 5)


def _enable_usajobs(monkeypatch, key="test-usajobs-key", email="example@example.com"):
    _silence_interval(monkeypatch)
    monkeypatch.setattr(settings, "usajobs_api_key", key)
    monkeypatch.setattr(settings, "usajobs_user_agent_email", email)
    monkeypatch.setattr(settings, "usajobs_max_pages", 3)


def _enable_muse(monkeypatch, key=None):
    _silence_interval(monkeypatch)
    monkeypatch.setattr(settings, "the_muse_api_key", key)
    monkeypatch.setattr(settings, "themuse_max_pages", 3)


@pytest.fixture(autouse=True)
def _clear_official_secrets(monkeypatch):
    """Each test starts with official sources unconfigured."""
    _silence_interval(monkeypatch)
    monkeypatch.setattr(settings, "usajobs_api_key", None)
    monkeypatch.setattr(settings, "usajobs_user_agent_email", None)
    monkeypatch.setattr(settings, "the_muse_api_key", None)
    monkeypatch.setattr(settings, "usajobs_max_pages", 3)
    monkeypatch.setattr(settings, "themuse_max_pages", 3)
    monkeypatch.delenv("USAJOBS_API_KEY", raising=False)
    monkeypatch.delenv("USAJOBS_USER_AGENT_EMAIL", raising=False)
    monkeypatch.delenv("THEMUSE_API_KEY", raising=False)
    monkeypatch.delenv("THE_MUSE_API_KEY", raising=False)


def test_credential_placeholder_is_unset():
    assert credential_present(None) is False
    assert credential_present("  ") is False
    assert credential_present("changeme") is False
    assert credential_present("your-api-key-here") is False
    assert credential_present("test-usajobs-key") is True


def test_dedupe_jobs_keeps_first_source_id():
    jobs = [
        {"source": "usajobs", "source_id": "usajobs:1", "title": "First"},
        {"source": "usajobs", "source_id": "usajobs:1", "title": "Second"},
        {"source": "the_muse", "source_id": "the_muse:1", "title": "Other source"},
        {"source": "usajobs", "source_id": "", "title": "Missing id"},
    ]
    kept = dedupe_jobs(jobs)
    assert [job["title"] for job in kept] == ["First", "Other source"]


def test_prefixed_source_ids_do_not_collide(db_session):
    db_session.add(
        JobListing(
            title="Federal role",
            company="Agency",
            source="usajobs",
            source_id="usajobs:1",
            url="https://www.usajobs.gov/job/1",
        )
    )
    db_session.add(
        JobListing(
            title="Startup role",
            company="Acme",
            source="the_muse",
            source_id="the_muse:1",
            url="https://www.themuse.com/jobs/acme/1",
        )
    )
    db_session.commit()
    assert db_session.query(JobListing).count() == 2


def test_sources_stay_registered_and_adzuna_remains():
    request = JobSearchRequest(query="python")
    assert "usajobs" in SUPPORTED_SOURCES
    assert "the_muse" in SUPPORTED_SOURCES
    assert "adzuna" in SUPPORTED_SOURCES
    assert "usajobs" in request.sources
    assert "the_muse" in request.sources
    assert "adzuna" in request.sources
    assert "usajobs" in DEFAULT_SCHEDULE_SOURCES
    assert "the_muse" in DEFAULT_SCHEDULE_SOURCES
    assert "adzuna" in DEFAULT_SCHEDULE_SOURCES


@pytest.mark.asyncio
async def test_usajobs_parses_fixture_and_sends_required_headers(monkeypatch):
    _enable_usajobs(monkeypatch)
    payload = _load("usajobs_page1.json")
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(USAJOBS_URL).mock(return_value=httpx.Response(200, json=payload))
        jobs = await USAJobsAPIClient().search_jobs(
            "software", "San Diego, California", limit=5
        )

    assert len(jobs) == 1
    job = jobs[0]
    assert job["source"] == "usajobs"
    assert job["source_id"] == "usajobs:21947200"
    assert job["url"] == "https://www.usajobs.gov/job/21947200"
    assert job["company"] == "Space and Naval Warfare Systems Command"
    assert job["location"] == "San Diego, California"
    assert "<script>" not in job["title"]
    assert "alert(1)" in job["title"]
    assert "<" not in job["description"]
    assert "Protect &amp; defend federal networks" == job["description"]
    assert job["salary_range"] == "92108-119746 Per Year"
    assert job["job_type"] == "Full Time"
    assert job["remote"] is True
    assert job["posted_date"] == "2016-06-05T00:00:00Z"
    assert job["requirements"] == "US citizenship"
    request = route.calls[0].request
    assert request.headers["Host"] == "data.usajobs.gov"
    assert request.headers["User-Agent"] == "example@example.com"
    assert request.headers["Authorization-Key"] == "test-usajobs-key"
    assert request.url.params["Keyword"] == "software"
    assert request.url.params["LocationName"] == "San Diego, California"
    assert request.url.params["Page"] == "1"
    assert "example@example.com" not in json.dumps(job)


@pytest.mark.asyncio
async def test_usajobs_paginates_until_limit_and_caps_pages(monkeypatch):
    _enable_usajobs(monkeypatch)
    page1 = _load("usajobs_page1.json")
    page2 = _load("usajobs_page2.json")
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(USAJOBS_URL).mock(
            side_effect=[
                httpx.Response(200, json=page1),
                httpx.Response(200, json=page2),
            ]
        )
        jobs = await USAJobsAPIClient().search_jobs("analyst", "Washington, DC", limit=10)

    assert [job["source_id"] for job in jobs] == ["usajobs:21947200", "usajobs:400"]
    assert [call.request.url.params["Page"] for call in route.calls] == ["1", "2"]

    monkeypatch.setattr(settings, "usajobs_max_pages", 1)
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(USAJOBS_URL).mock(return_value=httpx.Response(200, json=page1))
        capped = await USAJobsAPIClient().search_jobs("analyst", "Washington, DC", limit=10)
    assert [job["source_id"] for job in capped] == ["usajobs:21947200"]
    assert len(route.calls) == 1


@pytest.mark.asyncio
async def test_usajobs_disabled_when_key_or_email_missing(monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(USAJOBS_URL).mock(return_value=httpx.Response(200, json={}))
        jobs = await USAJobsAPIClient().search_jobs("software", "Remote", limit=5)
    assert jobs == []
    assert not route.called
    assert "USAJOBS_API_KEY" in caplog.text
    assert "USAJOBS_USER_AGENT_EMAIL" in caplog.text

    caplog.clear()
    _enable_usajobs(monkeypatch, key="changeme", email="person@example.com")
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(USAJOBS_URL).mock(return_value=httpx.Response(200, json={}))
        jobs = await USAJobsAPIClient().search_jobs("software", "Remote", limit=5)
    assert jobs == []
    assert not route.called
    assert "USAJOBS_API_KEY" in caplog.text
    assert "person@example.com" not in caplog.text

    caplog.clear()
    _enable_usajobs(monkeypatch, key="test-usajobs-key", email="not-an-email")
    jobs = await USAJobsAPIClient().search_jobs("software", "Remote", limit=5)
    assert jobs == []
    assert "USAJOBS_USER_AGENT_EMAIL" in caplog.text
    assert "test-usajobs-key" not in caplog.text


@pytest.mark.asyncio
async def test_usajobs_backs_off_on_429_then_parses(monkeypatch):
    _enable_usajobs(monkeypatch)
    monkeypatch.setattr(settings, "max_retries", 2)
    delays = []

    async def _sleep(seconds):
        delays.append(seconds)

    monkeypatch.setattr("app.services.api_clients.official_api.asyncio.sleep", _sleep)
    page = _load("usajobs_page2.json")
    page["SearchResult"]["UserArea"]["NumberOfPages"] = "1"
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(USAJOBS_URL).mock(
            side_effect=[
                httpx.Response(429, headers={"Retry-After": "2"}),
                httpx.Response(200, json=page),
            ]
        )
        jobs = await USAJobsAPIClient().search_jobs("analyst", "Washington, DC", limit=5)

    assert [job["source_id"] for job in jobs] == ["usajobs:400"]
    assert len(route.calls) == 2
    assert delays == [2]

    delays.clear()
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(USAJOBS_URL).mock(
            return_value=httpx.Response(429, headers={"Retry-After": "90"})
        )
        exhausted = await USAJobsAPIClient().search_jobs("analyst", "Washington, DC", limit=5)
    assert exhausted == []
    assert len(route.calls) == 3
    assert delays
    assert max(delays) <= 30


@pytest.mark.asyncio
async def test_usajobs_timeout_and_non_json_return_empty(monkeypatch):
    _enable_usajobs(monkeypatch)
    with respx.mock(assert_all_called=False) as mock:
        mock.get(USAJOBS_URL).mock(side_effect=httpx.TimeoutException("timed out"))
        assert await USAJobsAPIClient().search_jobs("software", "Remote", limit=5) == []

    with respx.mock(assert_all_called=False) as mock:
        mock.get(USAJOBS_URL).mock(
            return_value=httpx.Response(200, text="not-json")
        )
        assert await USAJobsAPIClient().search_jobs("software", "Remote", limit=5) == []


@pytest.mark.asyncio
async def test_muse_parses_without_key_and_filters_keywords(monkeypatch, caplog):
    _enable_muse(monkeypatch, key=None)
    caplog.set_level(logging.INFO)
    payload = _load("themuse_page1.json")
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(MUSE_URL).mock(return_value=httpx.Response(200, json=payload))
        jobs = await TheMuseAPIClient().search_jobs("python", "New York, NY", limit=10)

    assert [job["source_id"] for job in jobs] == ["the_muse:42"]
    job = jobs[0]
    assert job["source"] == "the_muse"
    assert job["url"] == "https://www.themuse.com/jobs/acme/python-engineer"
    assert job["company"] == "Acme &amp; Co"
    assert job["title"] == "Python Engineer"
    assert "<" not in job["title"]
    assert "onerror" not in job["title"]
    assert job["description"] == "Build APIs &amp; tools"
    assert job["location"] == "Flexible / Remote"
    assert job["remote"] is True
    assert job["job_type"] == "Mid Level"
    assert job["posted_date"] == "2024-01-15T00:00:00Z"
    request = route.calls[0].request
    assert "api_key" not in request.url.params
    assert request.url.params["page"] == "1"
    assert request.url.params["location"] == "New York, NY"
    assert "500" in caplog.text
    assert "THEMUSE_API_KEY" in caplog.text


@pytest.mark.asyncio
async def test_muse_sends_optional_key_and_known_category(monkeypatch, caplog):
    _enable_muse(monkeypatch, key="test-muse-key")
    caplog.set_level(logging.DEBUG)
    payload = _load("themuse_page1.json")
    payload["results"][0]["name"] = "Backend Developer"
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(MUSE_URL).mock(return_value=httpx.Response(200, json=payload))
        jobs = await TheMuseAPIClient().search_jobs(
            "Software Engineering", "Flexible / Remote", limit=5
        )
    assert any(job["source_id"] == "the_muse:42" for job in jobs)
    params = route.calls[0].request.url.params
    assert params["api_key"] == "test-muse-key"
    assert params["category"] == "Software Engineering"
    assert "test-muse-key" not in caplog.text


@pytest.mark.asyncio
async def test_muse_paginates_and_caps(monkeypatch):
    _enable_muse(monkeypatch)
    page1 = _load("themuse_page1.json")
    page2 = _load("themuse_page2.json")
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(MUSE_URL).mock(
            side_effect=[
                httpx.Response(200, json=page1),
                httpx.Response(200, json=page2),
            ]
        )
        jobs = await TheMuseAPIClient().search_jobs("python", "", limit=10)
    assert [job["source_id"] for job in jobs] == ["the_muse:42", "the_muse:99"]
    assert [call.request.url.params["page"] for call in route.calls] == ["1", "2"]

    monkeypatch.setattr(settings, "themuse_max_pages", 1)
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(MUSE_URL).mock(return_value=httpx.Response(200, json=page1))
        capped = await TheMuseAPIClient().search_jobs("python", "", limit=10)
    assert [job["source_id"] for job in capped] == ["the_muse:42"]
    assert len(route.calls) == 1


@pytest.mark.asyncio
async def test_muse_backs_off_on_429(monkeypatch):
    _enable_muse(monkeypatch, key="changeme")
    monkeypatch.setattr(settings, "max_retries", 1)
    delays = []

    async def _sleep(seconds):
        delays.append(seconds)

    monkeypatch.setattr("app.services.api_clients.official_api.asyncio.sleep", _sleep)
    page = _load("themuse_page2.json")
    page["page_count"] = 1
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(MUSE_URL).mock(
            side_effect=[
                httpx.Response(429, headers={"Retry-After": "1"}),
                httpx.Response(200, json=page),
            ]
        )
        jobs = await TheMuseAPIClient().search_jobs("", "", limit=5)
    assert [job["source_id"] for job in jobs] == ["the_muse:99"]
    assert delays == [1]
    assert "api_key" not in route.calls[0].request.url.params
    assert len(route.calls) == 2


@pytest.mark.asyncio
async def test_manager_does_not_scrape_official_sources(monkeypatch):
    _enable_usajobs(monkeypatch)
    called = {"browser": 0, "http": 0}

    async def _browser(*args, **kwargs):
        called["browser"] += 1
        return [{"title": "scraped", "company": "x", "url": "https://example.test", "source_id": "scraped"}]

    async def _http(*args, **kwargs):
        called["http"] += 1
        return [{"title": "scraped", "company": "x", "url": "https://example.test", "source_id": "scraped"}]

    payload = _load("usajobs_page2.json")
    with respx.mock(assert_all_called=False) as mock:
        mock.get(USAJOBS_URL).mock(return_value=httpx.Response(200, json=payload))
        manager = JobSourceManager()
        monkeypatch.setattr(manager, "search_via_browser", _browser)
        monkeypatch.setattr(manager, "search_via_http", _http)
        disabled = JobSourceManager()
        monkeypatch.setattr(settings, "usajobs_api_key", None)
        monkeypatch.setattr(settings, "usajobs_user_agent_email", None)
        # Rebuild so the disabled check sees the cleared credentials.
        disabled = JobSourceManager()
        monkeypatch.setattr(disabled, "search_via_browser", _browser)
        monkeypatch.setattr(disabled, "search_via_http", _http)
        missing = await disabled.search_jobs("analyst", "Washington, DC", ["usajobs"], limit=5)
        found = await manager.search_jobs("analyst", "Washington, DC", ["usajobs"], limit=5)

    assert missing == []
    assert called == {"browser": 0, "http": 0}
    assert [job["source_id"] for job in found] == ["usajobs:400"]
    assert manager.has_api_client("the_muse") is True
    assert disabled.has_api_client("usajobs") is False


@pytest.mark.asyncio
async def test_scheduler_stores_official_api_jobs(monkeypatch):
    saved = {}

    class _Query:
        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return None

    class _Session:
        def query(self, model):
            return _Query()

        def add(self, obj):
            saved["job"] = obj

        def commit(self):
            saved["committed"] = True

        def rollback(self):
            saved["rolled_back"] = True

        def close(self):
            saved["closed"] = True

    class _Matcher:
        def __init__(self, db):
            pass

        def calculate_match_score(self, description):
            return {
                "skill_match_score": 0.5,
                "experience_match_score": 0.5,
                "overall_match_score": 0.9,
            }

    async def _search(self, query, location, sources, limit=25):
        saved["sources"] = list(sources)
        saved["query"] = query
        return [
            {
                "title": "Python Engineer",
                "company": "Acme",
                "location": "Flexible / Remote",
                "source": "the_muse",
                "source_id": "the_muse:42",
                "url": "https://www.themuse.com/jobs/acme/python",
                "description": "Build APIs",
            }
        ]

    monkeypatch.setattr("app.services.scheduler.SessionLocal", lambda: _Session())
    monkeypatch.setattr("app.services.scheduler.SkillMatcher", _Matcher)
    monkeypatch.setattr(JobSourceManager, "search_jobs", _search)

    await run_scheduled_search(
        queries=["python"],
        location="Flexible / Remote",
        sources=["the_muse"],
        min_match_score=0.7,
        limit_per_query=5,
    )

    assert saved["sources"] == ["the_muse"]
    assert saved["query"] == "python"
    assert saved["job"].source == "the_muse"
    assert saved["job"].source_id == "the_muse:42"
    assert saved["job"].url == "https://www.themuse.com/jobs/acme/python"
    assert saved["committed"] is True
