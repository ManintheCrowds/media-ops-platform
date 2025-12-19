"""Mock HTTP responses for service clients."""

from typing import Dict, Any, List


def mock_seafile_libraries_response() -> List[Dict[str, Any]]:
    """Mock Seafile libraries response."""
    return [
        {
            "id": "abc123",
            "name": "My Library",
            "owner": "user@example.com",
            "size": 1024000,
            "encrypted": False
        },
        {
            "id": "def456",
            "name": "Shared Library",
            "owner": "admin@example.com",
            "size": 2048000,
            "encrypted": True
        }
    ]


def mock_jellyfin_libraries_response() -> List[Dict[str, Any]]:
    """Mock Jellyfin libraries response."""
    return [
        {
            "Name": "Movies",
            "CollectionType": "movies",
            "Id": "movies-123"
        },
        {
            "Name": "TV Shows",
            "CollectionType": "tvshows",
            "Id": "tv-456"
        }
    ]


def mock_jellyfin_recent_items_response(limit: int = 10) -> List[Dict[str, Any]]:
    """Mock Jellyfin recent items response."""
    return [
        {
            "Name": f"Movie {i}",
            "Type": "Movie",
            "Id": f"movie-{i}",
            "Year": 2020 + i
        }
        for i in range(limit)
    ]


def mock_bookstack_pages_response() -> List[Dict[str, Any]]:
    """Mock BookStack pages response."""
    return {
        "data": [
            {
                "id": 1,
                "name": "Getting Started",
                "slug": "getting-started",
                "book_id": 1
            },
            {
                "id": 2,
                "name": "API Documentation",
                "slug": "api-documentation",
                "book_id": 1
            }
        ]
    }


def mock_gitea_repositories_response() -> Dict[str, Any]:
    """Mock Gitea repositories response."""
    return {
        "data": [
            {
                "id": 1,
                "name": "my-repo",
                "full_name": "user/my-repo",
                "private": False,
                "html_url": "http://gitea:3000/user/my-repo"
            },
            {
                "id": 2,
                "name": "private-repo",
                "full_name": "user/private-repo",
                "private": True,
                "html_url": "http://gitea:3000/user/private-repo"
            }
        ]
    }


def mock_prometheus_query_response() -> Dict[str, Any]:
    """Mock Prometheus query response."""
    return {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"__name__": "up", "instance": "localhost:9090"},
                    "value": [1234567890, "1"]
                }
            ]
        }
    }


def mock_prometheus_metrics_response() -> Dict[str, Any]:
    """Mock Prometheus metrics list response."""
    return {
        "status": "success",
        "data": ["up", "cpu_usage", "memory_usage", "disk_usage"]
    }


def mock_grafana_dashboards_response() -> List[Dict[str, Any]]:
    """Mock Grafana dashboards response."""
    return [
        {
            "uid": "dashboard-1",
            "title": "System Overview",
            "url": "/d/dashboard-1/system-overview"
        },
        {
            "uid": "dashboard-2",
            "title": "Service Health",
            "url": "/d/dashboard-2/service-health"
        }
    ]


def mock_vaultwarden_stats_response() -> Dict[str, Any]:
    """Mock Vaultwarden stats response."""
    return {
        "object": "stats",
        "users": 10,
        "items": 150,
        "attachments": 25,
        "attachments_size": 10485760
    }
