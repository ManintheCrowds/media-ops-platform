"""Configuration for monitoring services."""

from pydantic_settings import BaseSettings


class PrometheusConfig(BaseSettings):
    """Prometheus configuration."""
    
    base_url: str = "http://prometheus:9090"
    
    class Config:
        env_prefix = "PROMETHEUS_"
        case_sensitive = False


class GrafanaConfig(BaseSettings):
    """Grafana configuration."""
    
    base_url: str = "http://grafana:3000"
    api_key: str = ""
    username: str = "admin"
    password: str = "admin"
    
    class Config:
        env_prefix = "GRAFANA_"
        case_sensitive = False


