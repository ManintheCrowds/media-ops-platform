"""Targeted tests for services.security.vaultwarden_client to improve coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from services.security.vaultwarden_client import VaultwardenClient
from services.security.config import VaultwardenConfig
from app.exceptions import VaultwardenError


def _json_response(data, status_code: int = 200):
    response = MagicMock()
    response.status_code = status_code
    response.json = MagicMock(return_value=data)
    return response


@pytest.mark.unit
class TestVaultwardenClient:
    """Cover VaultwardenClient session and error paths."""

    def test_build_headers_with_token(self):
        config = VaultwardenConfig(base_url="http://vaultwarden:80", admin_token="secret")
        client = VaultwardenClient(config=config)
        headers = client._build_headers()
        assert headers["X-Vaultwarden-Admin-Token"] == "secret"

    def test_build_headers_without_token(self):
        config = VaultwardenConfig(base_url="http://vaultwarden:80", admin_token=None)
        client = VaultwardenClient(config=config)
        assert client._build_headers() == {}

    @pytest.mark.asyncio
    async def test_get_users_success(self):
        async with VaultwardenClient() as client:
            client._session.get = AsyncMock(return_value=_json_response([{"id": "1"}]))
            users = await client.get_users()
        assert users == [{"id": "1"}]

    @pytest.mark.asyncio
    async def test_get_users_non_list_response(self):
        async with VaultwardenClient() as client:
            client._session.get = AsyncMock(return_value=_json_response({}, status_code=500))
            users = await client.get_users()
        assert users == []

    @pytest.mark.asyncio
    async def test_get_user_success(self):
        async with VaultwardenClient() as client:
            client._session.get = AsyncMock(return_value=_json_response({"id": "u1"}))
            user = await client.get_user("u1")
        assert user == {"id": "u1"}

    @pytest.mark.asyncio
    async def test_get_user_error_raises(self):
        async with VaultwardenClient() as client:
            client._session.get = AsyncMock(return_value=_json_response({}, status_code=404))
            with pytest.raises(VaultwardenError):
                await client.get_user("u1")

    @pytest.mark.asyncio
    async def test_get_stats_success(self):
        async with VaultwardenClient() as client:
            client._session.get = AsyncMock(return_value=_json_response({"users": 2}))
            stats = await client.get_stats()
        assert stats == {"users": 2}

    @pytest.mark.asyncio
    async def test_get_stats_http_error_raises(self):
        async with VaultwardenClient() as client:
            client._session.get = AsyncMock(side_effect=Exception("network"))
            with pytest.raises(VaultwardenError):
                await client.get_stats()
