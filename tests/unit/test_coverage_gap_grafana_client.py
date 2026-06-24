"""Targeted tests for services.monitoring.grafana_client to improve coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from services.monitoring.grafana_client import GrafanaClient
from services.monitoring.config import GrafanaConfig
from app.exceptions import GrafanaError


def _json_response(data, status_code: int = 200):
    response = MagicMock()
    response.status_code = status_code
    response.json = MagicMock(return_value=data)
    return response


@pytest.mark.unit
class TestGrafanaClient:
    """Cover GrafanaClient auth branches and API methods."""

    def test_build_headers_with_api_key(self):
        config = GrafanaConfig(base_url="http://grafana:3000", api_key="grafana-key")
        client = GrafanaClient(config=config)
        headers = client._build_headers()
        assert headers["Authorization"] == "Bearer grafana-key"

    def test_build_headers_basic_auth_without_api_key(self):
        config = GrafanaConfig(
            base_url="http://grafana:3000",
            api_key=None,
            username="admin",
            password="admin",
        )
        client = GrafanaClient(config=config)
        headers = client._build_headers()
        assert headers["Authorization"].startswith("Basic ")

    @pytest.mark.asyncio
    async def test_ping_success(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=MagicMock(status_code=200))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            assert await GrafanaClient().ping() is True

    @pytest.mark.asyncio
    async def test_get_dashboards_success(self):
        async with GrafanaClient() as client:
            client._session.get = AsyncMock(
                return_value=_json_response([{"uid": "dash1"}])
            )
            dashboards = await client.get_dashboards()
        assert dashboards == [{"uid": "dash1"}]

    @pytest.mark.asyncio
    async def test_get_dashboards_non_list_returns_empty(self):
        async with GrafanaClient() as client:
            client._session.get = AsyncMock(return_value=_json_response({}, status_code=500))
            dashboards = await client.get_dashboards()
        assert dashboards == []

    @pytest.mark.asyncio
    async def test_get_dashboard_success(self):
        async with GrafanaClient() as client:
            client._session.get = AsyncMock(return_value=_json_response({"dashboard": {}}))
            dashboard = await client.get_dashboard("dash1")
        assert dashboard == {"dashboard": {}}

    @pytest.mark.asyncio
    async def test_get_dashboard_error_raises(self):
        async with GrafanaClient() as client:
            client._session.get = AsyncMock(return_value=_json_response({}, status_code=404))
            with pytest.raises(GrafanaError):
                await client.get_dashboard("dash1")

    @pytest.mark.asyncio
    async def test_get_datasources_success(self):
        async with GrafanaClient() as client:
            client._session.get = AsyncMock(
                return_value=_json_response([{"name": "Prometheus"}])
            )
            sources = await client.get_datasources()
        assert sources == [{"name": "Prometheus"}]

    @pytest.mark.asyncio
    async def test_get_datasources_non_list_returns_empty(self):
        async with GrafanaClient() as client:
            client._session.get = AsyncMock(return_value=_json_response({}, status_code=500))
            sources = await client.get_datasources()
        assert sources == []
