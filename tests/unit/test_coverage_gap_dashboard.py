"""Targeted tests for services.monitoring.dashboard to improve coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from services.monitoring.dashboard import MonitoringDashboard
from services.monitoring.prometheus_client import PrometheusClient
from services.monitoring.grafana_client import GrafanaClient


@pytest.mark.unit
class TestMonitoringDashboard:
    """Test MonitoringDashboard class to cover untested code."""
    
    @pytest.mark.asyncio
    async def test_init(self):
        """Test MonitoringDashboard initialization."""
        prometheus_client = MagicMock(spec=PrometheusClient)
        grafana_client = MagicMock(spec=GrafanaClient)
        
        dashboard = MonitoringDashboard(prometheus_client, grafana_client)
        
        assert dashboard.prometheus == prometheus_client
        assert dashboard.grafana == grafana_client
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_success(self):
        """Test get_system_metrics with successful queries."""
        prometheus_client = MagicMock(spec=PrometheusClient)
        grafana_client = MagicMock(spec=GrafanaClient)
        
        # Mock Prometheus query responses
        prometheus_client.query = AsyncMock(side_effect=[
            {"status": "success", "data": {"result": [{"value": [1234567890, "75.5"]}]}},  # CPU
            {"status": "success", "data": {"result": [{"value": [1234567890, "60.2"]}]}},  # Memory
            {"status": "success", "data": {"result": [{"value": [1234567890, "45.8"]}]}}  # Disk
        ])
        
        dashboard = MonitoringDashboard(prometheus_client, grafana_client)
        metrics = await dashboard.get_system_metrics()
        
        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        assert "disk_usage" in metrics
        assert prometheus_client.query.call_count == 3
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_partial_results(self):
        """Test get_system_metrics with some failed queries."""
        prometheus_client = MagicMock(spec=PrometheusClient)
        grafana_client = MagicMock(spec=GrafanaClient)
        
        # Mock Prometheus query responses - some return None
        prometheus_client.query = AsyncMock(side_effect=[
            {"status": "success", "data": {"result": [{"value": [1234567890, "75.5"]}]}},  # CPU success
            None,  # Memory fails
            {"status": "success", "data": {"result": [{"value": [1234567890, "45.8"]}]}}  # Disk success
        ])
        
        dashboard = MonitoringDashboard(prometheus_client, grafana_client)
        metrics = await dashboard.get_system_metrics()
        
        assert "cpu_usage" in metrics
        assert "memory_usage" not in metrics
        assert "disk_usage" in metrics
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_all_fail(self):
        """Test get_system_metrics when all queries fail."""
        prometheus_client = MagicMock(spec=PrometheusClient)
        grafana_client = MagicMock(spec=GrafanaClient)
        
        prometheus_client.query = AsyncMock(return_value=None)
        
        dashboard = MonitoringDashboard(prometheus_client, grafana_client)
        metrics = await dashboard.get_system_metrics()
        
        assert metrics == {}
    
    @pytest.mark.asyncio
    async def test_get_service_status_success(self):
        """Test get_service_status with active targets."""
        prometheus_client = MagicMock(spec=PrometheusClient)
        grafana_client = MagicMock(spec=GrafanaClient)
        
        mock_targets = {
            "data": {
                "activeTargets": [
                    {"health": "up", "labels": {"job": "service1"}},
                    {"health": "up", "labels": {"job": "service2"}},
                    {"health": "down", "labels": {"job": "service3"}}
                ]
            }
        }
        prometheus_client.get_targets = AsyncMock(return_value=mock_targets)
        
        dashboard = MonitoringDashboard(prometheus_client, grafana_client)
        status = await dashboard.get_service_status()
        
        assert status["total"] == 3
        assert status["healthy"] == 2
        assert status["unhealthy"] == 1
        assert len(status["targets"]) == 3
    
    @pytest.mark.asyncio
    async def test_get_service_status_no_targets(self):
        """Test get_service_status when no targets exist."""
        prometheus_client = MagicMock(spec=PrometheusClient)
        grafana_client = MagicMock(spec=GrafanaClient)
        
        prometheus_client.get_targets = AsyncMock(return_value=None)
        
        dashboard = MonitoringDashboard(prometheus_client, grafana_client)
        status = await dashboard.get_service_status()
        
        assert status["total"] == 0
        assert status["healthy"] == 0
        assert status["unhealthy"] == 0
        assert status["targets"] == []
    
    @pytest.mark.asyncio
    async def test_get_service_status_empty_data(self):
        """Test get_service_status when targets data is empty."""
        prometheus_client = MagicMock(spec=PrometheusClient)
        grafana_client = MagicMock(spec=GrafanaClient)
        
        prometheus_client.get_targets = AsyncMock(return_value={"data": {}})
        
        dashboard = MonitoringDashboard(prometheus_client, grafana_client)
        status = await dashboard.get_service_status()
        
        assert status["total"] == 0
        assert status["healthy"] == 0
        assert status["unhealthy"] == 0
        assert status["targets"] == []

