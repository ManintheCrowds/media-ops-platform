"""Grafana dashboard integration."""

import json
from typing import Dict, Any, List
from pathlib import Path


class GrafanaDashboardManager:
    """Grafana dashboard provisioning and management."""
    
    def __init__(self, dashboards_dir: str = "grafana/dashboards"):
        self.dashboards_dir = Path(dashboards_dir)
        self.dashboards_dir.mkdir(parents=True, exist_ok=True)
        
    def create_security_overview_dashboard(self) -> Dict[str, Any]:
        """Create security overview dashboard JSON."""
        dashboard = {
            "dashboard": {
                "title": "Security Overview",
                "tags": ["security"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Security Events (24h)",
                        "type": "stat",
                        "targets": [{
                            "expr": "security_events_total",
                            "legendFormat": "Total Events"
                        }]
                    },
                    {
                        "id": 2,
                        "title": "Active Incidents",
                        "type": "stat",
                        "targets": [{
                            "expr": "incidents_active",
                            "legendFormat": "Active"
                        }]
                    },
                    {
                        "id": 3,
                        "title": "Blocked IPs",
                        "type": "stat",
                        "targets": [{
                            "expr": "blocked_ips_total",
                            "legendFormat": "Blocked"
                        }]
                    },
                    {
                        "id": 4,
                        "title": "Threat Level",
                        "type": "gauge",
                        "targets": [{
                            "expr": "security_alerts_active",
                            "legendFormat": "Alerts"
                        }]
                    }
                ],
                "refresh": "30s"
            }
        }
        return dashboard
    
    def create_intrusion_detection_dashboard(self) -> Dict[str, Any]:
        """Create intrusion detection dashboard."""
        dashboard = {
            "dashboard": {
                "title": "Intrusion Detection",
                "tags": ["security", "ids"],
                "panels": [
                    {
                        "id": 1,
                        "title": "Intrusion Attempts by Type",
                        "type": "piechart",
                        "targets": [{
                            "expr": "intrusion_attempts_total",
                            "legendFormat": "{{attack_type}}"
                        }]
                    },
                    {
                        "id": 2,
                        "title": "Top Attacking IPs",
                        "type": "table",
                        "targets": [{
                            "expr": "topk(10, security_events_total{event_type=\"intrusion_attempt\"})",
                            "legendFormat": "{{source_ip}}"
                        }]
                    },
                    {
                        "id": 3,
                        "title": "Attack Timeline",
                        "type": "graph",
                        "targets": [{
                            "expr": "rate(security_events_total[5m])",
                            "legendFormat": "{{event_type}}"
                        }]
                    }
                ]
            }
        }
        return dashboard
    
    def save_dashboard(self, dashboard: Dict[str, Any], filename: str):
        """Save dashboard JSON to file."""
        filepath = self.dashboards_dir / filename
        with open(filepath, 'w') as f:
            json.dump(dashboard, f, indent=2)
    
    def get_all_dashboards(self) -> List[Dict[str, Any]]:
        """Get all dashboard definitions."""
        dashboards = []
        
        # Create default dashboards
        dashboards.append(self.create_security_overview_dashboard())
        dashboards.append(self.create_intrusion_detection_dashboard())
        
        return dashboards
