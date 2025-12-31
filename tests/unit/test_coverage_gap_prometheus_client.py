"""Targeted tests for services.monitoring.prometheus_client to improve coverage."""

import pytest
import respx
import httpx
from services.monitoring.prometheus_client import PrometheusClient


@pytest.mark.unit
class TestPrometheusClientErrorHandling:
    """Test PrometheusClient error handling paths to cover untested code."""
    
    @pytest.mark.asyncio
    async def test_ping_failure(self):
        """Test ping when Prometheus is not accessible (covers line 33-34)."""
        with respx.mock:
            respx.get("http://prometheus:9090/-/healthy").mock(side_effect=httpx.RequestError("Connection failed"))
            client = PrometheusClient()
            result = await client.ping()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_query_without_session_creates_session(self):
        """Test query when _session is None (covers line 39-40)."""
        mock_response = {"status": "success", "data": {"result": []}}
        with respx.mock:
            respx.get("http://prometheus:9090/api/v1/query").mock(
                return_value=httpx.Response(200, json=mock_response)
            )
            client = PrometheusClient()
            # Call query without entering context manager
            result = await client.query("up")
            assert result is not None
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_query_exception_handling(self):
        """Test query when exception occurs (covers line 49-51)."""
        with respx.mock:
            respx.get("http://prometheus:9090/api/v1/query").mock(
                side_effect=httpx.RequestError("Request failed")
            )
            async with PrometheusClient() as client:
                result = await client.query("up")
                assert result is None
    
    @pytest.mark.asyncio
    async def test_query_range_without_session_creates_session(self):
        """Test query_range when _session is None (covers line 55-57)."""
        mock_response = {"status": "success", "data": {"result": []}}
        with respx.mock:
            respx.get("http://prometheus:9090/api/v1/query_range").mock(
                return_value=httpx.Response(200, json=mock_response)
            )
            client = PrometheusClient()
            result = await client.query_range("up", "2023-01-01T00:00:00Z", "2023-01-01T01:00:00Z")
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_query_range_exception_handling(self):
        """Test query_range when exception occurs (covers line 71-73)."""
        with respx.mock:
            respx.get("http://prometheus:9090/api/v1/query_range").mock(
                side_effect=httpx.RequestError("Request failed")
            )
            async with PrometheusClient() as client:
                result = await client.query_range("up", "2023-01-01T00:00:00Z", "2023-01-01T01:00:00Z")
                assert result is None
    
    @pytest.mark.asyncio
    async def test_get_targets_without_session_creates_session(self):
        """Test get_targets when _session is None (covers line 77-79)."""
        mock_response = {"status": "success", "data": {"activeTargets": []}}
        with respx.mock:
            respx.get("http://prometheus:9090/api/v1/targets").mock(
                return_value=httpx.Response(200, json=mock_response)
            )
            client = PrometheusClient()
            result = await client.get_targets()
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_targets_exception_handling(self):
        """Test get_targets when exception occurs (covers line 85-87)."""
        with respx.mock:
            respx.get("http://prometheus:9090/api/v1/targets").mock(
                side_effect=httpx.RequestError("Request failed")
            )
            async with PrometheusClient() as client:
                result = await client.get_targets()
                assert result is None
    
    @pytest.mark.asyncio
    async def test_get_metrics_exception_handling(self):
        """Test get_metrics when exception occurs (covers line 97-99)."""
        with respx.mock:
            respx.get("http://prometheus:9090/api/v1/label/__name__/values").mock(
                side_effect=httpx.RequestError("Request failed")
            )
            client = PrometheusClient()
            metrics = await client.get_metrics()
            assert metrics == []

