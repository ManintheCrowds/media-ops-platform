"""Mock service configurations for testing."""

from typing import Dict, Any


def mock_seafile_config() -> Dict[str, Any]:
    """Mock Seafile configuration."""
    return {
        "base_url": "http://seafile:8000",
        "api_token": "test-seafile-token"
    }


def mock_jellyfin_config() -> Dict[str, Any]:
    """Mock Jellyfin configuration."""
    return {
        "base_url": "http://jellyfin:8096",
        "api_key": "test-jellyfin-key"
    }


def mock_bookstack_config() -> Dict[str, Any]:
    """Mock BookStack configuration."""
    return {
        "base_url": "http://bookstack:8002",
        "api_token": "test-bookstack-token",
        "api_id": "test-id",
        "api_secret": "test-secret"
    }


def mock_gitea_config() -> Dict[str, Any]:
    """Mock Gitea configuration."""
    return {
        "base_url": "http://gitea:3000",
        "api_token": "test-gitea-token"
    }


def mock_prometheus_config() -> Dict[str, Any]:
    """Mock Prometheus configuration."""
    return {
        "base_url": "http://prometheus:9090"
    }


def mock_grafana_config() -> Dict[str, Any]:
    """Mock Grafana configuration."""
    return {
        "base_url": "http://grafana:3000",
        "username": "admin",
        "password": "admin",
        "api_key": None
    }


def mock_vaultwarden_config() -> Dict[str, Any]:
    """Mock Vaultwarden configuration."""
    return {
        "base_url": "http://vaultwarden:80",
        "admin_token": "test-vaultwarden-admin-token"
    }
