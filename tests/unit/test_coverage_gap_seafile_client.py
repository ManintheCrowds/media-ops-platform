"""Targeted tests for services.file_storage.seafile_client to improve coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from services.file_storage.seafile_client import SeafileClient
from app.exceptions import SeafileError


def _json_response(data, status_code: int = 200):
    response = MagicMock()
    response.status_code = status_code
    response.json = MagicMock(return_value=data)
    return response


@pytest.mark.unit
class TestSeafileClient:
    """Cover SeafileClient auth and library methods."""

    @pytest.mark.asyncio
    async def test_get_auth_token_success(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=_json_response({"token": "abc"}))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            token = await SeafileClient().get_auth_token("user", "pass")
        assert token == "abc"

    @pytest.mark.asyncio
    async def test_get_auth_token_unauthorized_raises(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=_json_response({}, status_code=401))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            with pytest.raises(SeafileError, match="Authentication failed"):
                await SeafileClient().get_auth_token("user", "bad")

    @pytest.mark.asyncio
    async def test_get_libraries_success(self):
        async with SeafileClient() as client:
            client._session.get = AsyncMock(return_value=_json_response([{"name": "lib"}]))
            libraries = await client.get_libraries()
        assert libraries == [{"name": "lib"}]

    @pytest.mark.asyncio
    async def test_get_library_info_success(self):
        async with SeafileClient() as client:
            client._session.get = AsyncMock(return_value=_json_response({"id": "r1"}))
            info = await client.get_library_info("r1")
        assert info == {"id": "r1"}

    @pytest.mark.asyncio
    async def test_create_library_success(self):
        async with SeafileClient() as client:
            client._session.post = AsyncMock(return_value=_json_response({"id": "new"}, status_code=201))
            library = await client.create_library("Docs", "desc")
        assert library == {"id": "new"}

    @pytest.mark.asyncio
    async def test_create_library_error_raises(self):
        async with SeafileClient() as client:
            client._session.post = AsyncMock(return_value=_json_response({}, status_code=500))
            with pytest.raises(SeafileError):
                await client.create_library("Docs")
