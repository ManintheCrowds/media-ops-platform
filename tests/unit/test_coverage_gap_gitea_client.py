"""Targeted tests for services.dev_tools.gitea_client to improve coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from services.dev_tools.gitea_client import GiteaClient
from services.dev_tools.config import GiteaConfig
from app.exceptions import GiteaError


def _json_response(data, status_code: int = 200):
    response = MagicMock()
    response.status_code = status_code
    response.json = MagicMock(return_value=data)
    return response


@pytest.mark.unit
class TestGiteaClient:
    """Cover GiteaClient version and repository methods."""

    def test_build_headers_with_token(self):
        config = GiteaConfig(base_url="http://gitea:3000", api_token="abc123")
        client = GiteaClient(config=config)
        assert client._build_headers()["Authorization"] == "token abc123"

    @pytest.mark.asyncio
    async def test_get_version_success(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                return_value=_json_response({"version": "1.21"})
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            version = await GiteaClient().get_version()
        assert version == {"version": "1.21"}

    @pytest.mark.asyncio
    async def test_get_version_http_error_raises(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=_json_response({}, status_code=500))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            with pytest.raises(GiteaError):
                await GiteaClient().get_version()

    @pytest.mark.asyncio
    async def test_get_version_request_error_raises(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.RequestError("down"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            with pytest.raises(GiteaError):
                await GiteaClient().get_version()

    @pytest.mark.asyncio
    async def test_get_repositories_success(self):
        async with GiteaClient() as client:
            client._session.get = AsyncMock(
                return_value=_json_response({"data": [{"name": "repo1"}]})
            )
            repos = await client.get_repositories()
        assert repos == [{"name": "repo1"}]

    @pytest.mark.asyncio
    async def test_get_user_repositories_success(self):
        async with GiteaClient() as client:
            client._session.get = AsyncMock(return_value=_json_response([{"name": "mine"}]))
            repos = await client.get_user_repositories("alice")
        assert repos == [{"name": "mine"}]

    @pytest.mark.asyncio
    async def test_create_repository_success(self):
        async with GiteaClient() as client:
            client._session.post = AsyncMock(
                return_value=_json_response({"name": "new-repo"}, status_code=201)
            )
            repo = await client.create_repository("new-repo", description="desc")
        assert repo == {"name": "new-repo"}

    @pytest.mark.asyncio
    async def test_get_repository_success(self):
        async with GiteaClient() as client:
            client._session.get = AsyncMock(return_value=_json_response({"name": "repo1"}))
            repo = await client.get_repository("alice", "repo1")
        assert repo == {"name": "repo1"}

    @pytest.mark.asyncio
    async def test_get_repository_error_raises(self):
        async with GiteaClient() as client:
            client._session.get = AsyncMock(return_value=_json_response({}, status_code=404))
            with pytest.raises(GiteaError):
                await client.get_repository("alice", "missing")
