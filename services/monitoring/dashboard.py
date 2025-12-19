"""Custom monitoring dashboard utilities."""

from typing import Dict, List, Any
from services.monitoring.prometheus_client import PrometheusClient
from services.monitoring.grafana_client import GrafanaClient


class MonitoringDashboard:
    """Custom monitoring dashboard aggregator."""
    
    def __init__(self, prometheus_client: PrometheusClient, grafana_client: GrafanaClient):
        self.prometheus = prometheus_client
        self.grafana = grafana_client
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get aggregated system metrics."""
        metrics = {}
        
        # CPU usage
        cpu_query = '100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
        cpu_result = await self.prometheus.query(cpu_query)
        if cpu_result:
            metrics["cpu_usage"] = cpu_result
        
        # Memory usage
        memory_query = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
        memory_result = await self.prometheus.query(memory_query)
        if memory_result:
            metrics["memory_usage"] = memory_result
        
        # Disk usage
        disk_query = '(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100'
        disk_result = await self.prometheus.query(disk_query)
        if disk_result:
            metrics["disk_usage"] = disk_result
        
        return metrics
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get status of all monitored services."""
        targets = await self.prometheus.get_targets()
        if targets and "data" in targets:
            active_targets = targets["data"].get("activeTargets", [])
            return {
                "total": len(active_targets),
                "healthy": sum(1 for t in active_targets if t.get("health") == "up"),
                "unhealthy": sum(1 for t in active_targets if t.get("health") == "down"),
                "targets": active_targets
            }
        return {"total": 0, "healthy": 0, "unhealthy": 0, "targets": []}


