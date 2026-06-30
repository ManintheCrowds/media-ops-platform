"""Targeted tests for services.media_server.jellyfin_client to improve coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from services.media_server.jellyfin_client import JellyfinClient
from app.exceptions import JellyfinError


def _json_response(data, status_code: int = 200):
    response = MagicMock()
    response.status_code = status_code
    response.json = MagicMock(return_value=data)
    return response


@pytest.mark.unit
class TestJellyfinClient:
    """Cover JellyfinClient auth and library methods."""

    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=_json_response({"AccessToken": "tok"}))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            token = await JellyfinClient().authenticate("user", "pass")
        assert token == "tok"

    @pytest.mark.asyncio
    async def test_authenticate_unauthorized_raises(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=_json_response({}, status_code=401))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            with pytest.raises(JellyfinError, match="Authentication failed"):
                await JellyfinClient().authenticate("user", "bad")

    @pytest.mark.asyncio
    async def test_get_server_info_success(self):
        async with JellyfinClient() as client:
            client._session.get = AsyncMock(return_value=_json_response({"ServerName": "JF"}))
            info = await client.get_server_info()
        assert info == {"ServerName": "JF"}

    @pytest.mark.asyncio
    async def test_get_libraries_success(self):
        async with JellyfinClient() as client:
            client._session.get = AsyncMock(return_value=_json_response([{"Name": "Movies"}]))
            libraries = await client.get_libraries()
        assert libraries == [{"Name": "Movies"}]

    @pytest.mark.asyncio
    async def test_get_recent_items_success(self):
        async with JellyfinClient() as client:
            client._session.get = AsyncMock(return_value=_json_response([{"Id": "1"}]))
            items = await client.get_recent_items(limit=5)
        assert items == [{"Id": "1"}]

    @pytest.mark.asyncio
    async def test_get_server_info_error_raises(self):
        async with JellyfinClient() as client:
            client._session.get = AsyncMock(return_value=_json_response({}, status_code=500))
            with pytest.raises(JellyfinError):
                await client.get_server_info()
