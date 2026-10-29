"""Adzuna credentials come from the environment and fail closed when missing."""

import pytest

from app.config import settings
from app.services.api_clients.adzuna_api import (
    AdzunaAPIClient,
    AdzunaCredentialsError,
    adzuna_credentials_message,
    missing_adzuna_env_names,
)
from app.services.job_source_manager import JobSourceManager


@pytest.fixture
def unset_adzuna(monkeypatch):
    """Clear Adzuna settings so tests do not depend on a developer .env."""
    monkeypatch.setattr(settings, "adzuna_api_id", None)
    monkeypatch.setattr(settings, "adzuna_api_key", None)


@pytest.mark.asyncio
async def test_search_fails_when_credentials_missing(unset_adzuna):
    """A search names the env vars to set and does not call the network."""
    client = AdzunaAPIClient()
    try:
        with pytest.raises(AdzunaCredentialsError) as exc_info:
            await client.search_jobs("python", "Minneapolis, MN", 1)
    finally:
        await client.close()

    message = str(exc_info.value)
    assert message == adzuna_credentials_message(["ADZUNA_API_ID", "ADZUNA_API_KEY"])
    assert "ADZUNA_API_ID" in message
    assert "ADZUNA_API_KEY" in message
    assert missing_adzuna_env_names() == ["ADZUNA_API_ID", "ADZUNA_API_KEY"]


@pytest.mark.asyncio
async def test_placeholder_credentials_are_treated_as_missing(monkeypatch):
    """Example-file placeholders are not live credentials."""
    monkeypatch.setattr(settings, "adzuna_api_id", "changeme")
    monkeypatch.setattr(settings, "adzuna_api_key", "changeme")
    client = AdzunaAPIClient()
    try:
        with pytest.raises(AdzunaCredentialsError):
            await client.search_jobs("python", "Minneapolis, MN", 1)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_adzuna_only_search_fails_when_unconfigured(unset_adzuna):
    """Requesting only Adzuna without env vars raises a clear error."""
    manager = JobSourceManager()
    try:
        assert manager.has_api_client("adzuna") is False
        with pytest.raises(AdzunaCredentialsError) as exc_info:
            await manager.search_jobs("python", "Minneapolis, MN", ["adzuna"], 1)
    finally:
        await manager.close()

    assert "ADZUNA_API_ID" in str(exc_info.value)
    assert "ADZUNA_API_KEY" in str(exc_info.value)
