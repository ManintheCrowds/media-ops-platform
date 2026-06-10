"""Targeted tests for services.monitoring.prometheus_client to improve coverage."""

import pytest
import respx
import httpx
import re
from unittest.mock import AsyncMock, patch
from services.monitoring.prometheus_client import PrometheusClient


def mock_get(respx_mock, pattern: str, **kwargs):
    """Register a GET mock for service client HTTP calls."""
    if pattern.startswith("http"):
        normalized = re.sub(r":80(?=/|\.\*|$)", "", pattern)
        url_prefix = normalized[:-2] if normalized.endswith(".*") else normalized
        respx_mock.route(url__startswith=url_prefix).mock(**kwargs)
    else:
        respx_mock.route(url__regex=pattern).mock(**kwargs)


@pytest.mark.unit
class TestPrometheusClientErrorHandling:
    """Test PrometheusClient error handling paths to cover untested code."""
    
    @pytest.mark.asyncio
    async def test_ping_failure(self, respx_mock):
        """Test ping when Prometheus is not accessible (covers line 33-34)."""
        mock_get(respx_mock, r"http://prometheus:9090/-/healthy.*", side_effect=httpx.RequestError("Connection failed"))
        client = PrometheusClient()
        result = await client.ping()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_query_without_session_creates_session(self, respx_mock):
        """Test query when _session is None (covers line 39-40)."""
        mock_response = {"status": "success", "data": {"result": []}}
        mock_get(
            respx_mock,
            r"http://prometheus:9090/api/v1/query.*",
            return_value=httpx.Response(200, json=mock_response)
        )
        client = PrometheusClient()
        # Call query without entering context manager
        result = await client.query("up")
        assert result is not None
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_query_exception_handling(self, respx_mock):
        """Test query when exception occurs (covers line 49-51)."""
        mock_get(
            respx_mock,
            r"http://prometheus:9090/api/v1/query.*",
            side_effect=httpx.RequestError("Request failed")
        )
        async with PrometheusClient() as client:
            result = await client.query("up")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_query_range_without_session_creates_session(self, respx_mock):
        """Test query_range when _session is None (covers line 55-57)."""
        mock_response = {"status": "success", "data": {"result": []}}
        mock_get(
            respx_mock,
            r"http://prometheus:9090/api/v1/query_range.*",
            return_value=httpx.Response(200, json=mock_response)
        )
        client = PrometheusClient()
        result = await client.query_range("up", "2023-01-01T00:00:00Z", "2023-01-01T01:00:00Z")
        assert result is not None

    @pytest.mark.asyncio
    async def test_query_range_exception_handling(self, respx_mock):
        """Test query_range when exception occurs (covers line 71-73)."""
        mock_get(
            respx_mock,
            r"http://prometheus:9090/api/v1/query_range.*",
            side_effect=httpx.RequestError("Request failed")
        )
        async with PrometheusClient() as client:
            result = await client.query_range("up", "2023-01-01T00:00:00Z", "2023-01-01T01:00:00Z")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_targets_without_session_creates_session(self, respx_mock):
        """Test get_targets when _session is None (covers line 77-79)."""
        mock_response = {"status": "success", "data": {"activeTargets": []}}
        mock_get(
            respx_mock,
            r"http://prometheus:9090/api/v1/targets.*",
            return_value=httpx.Response(200, json=mock_response)
        )
        client = PrometheusClient()
        result = await client.get_targets()
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_targets_exception_handling(self, respx_mock):
        """Test get_targets when exception occurs (covers line 85-87)."""
        mock_get(
            respx_mock,
            r"http://prometheus:9090/api/v1/targets.*",
            side_effect=httpx.RequestError("Request failed")
        )
        async with PrometheusClient() as client:
            result = await client.get_targets()
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_metrics_success(self):
        """Test get_metrics successful response (covers lines 76-78)."""
        client = PrometheusClient()
        mock_response = httpx.Response(200, json={"data": ["metric1", "metric2", "metric3"]})
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            metrics = await client.get_metrics()
        assert metrics == ["metric1", "metric2", "metric3"]

    @pytest.mark.asyncio
    async def test_get_metrics_http_error(self):
        """Test get_metrics when HTTPError occurs (covers line 79-81)."""
        client = PrometheusClient()
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.HTTPError("HTTP error"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            metrics = await client.get_metrics()
        assert metrics == []

    @pytest.mark.asyncio
    async def test_get_metrics_timeout_exception(self):
        """Test get_metrics when TimeoutException occurs (covers lines 82-84)."""
        client = PrometheusClient()
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            metrics = await client.get_metrics()
        assert metrics == []

    @pytest.mark.asyncio
    async def test_get_metrics_general_exception(self):
        """Test get_metrics when general exception occurs (covers lines 85-87)."""
        client = PrometheusClient()
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Unexpected error"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            metrics = await client.get_metrics()
        assert metrics == []

