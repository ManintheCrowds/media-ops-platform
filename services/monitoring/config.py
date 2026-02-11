"""Configuration for monitoring services."""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from urllib.parse import urlparse
from app.config_base import BaseServiceConfig


class PrometheusConfig(BaseServiceConfig):
    """Prometheus configuration."""
    
    base_url: str = "http://prometheus:9090"
    
    class Config:
        env_prefix = "PROMETHEUS_"
        case_sensitive = False
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate base URL format."""
        try:
            result = urlparse(v)
            if not result.scheme or not result.netloc:
                raise ValueError(f"Invalid URL format for base_url: {v}")
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Invalid URL format for base_url: {v}")
        return v


class GrafanaConfig(BaseServiceConfig):
    """Grafana configuration."""
    
    base_url: str = "http://grafana:3000"
    api_key: Optional[str] = None
    username: str = "admin"
    password: str = "admin"
    
    class Config:
        env_prefix = "GRAFANA_"
        case_sensitive = False
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate base URL format."""
        try:
            result = urlparse(v)
            if not result.scheme or not result.netloc:
                raise ValueError(f"Invalid URL format for base_url: {v}")
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Invalid URL format for base_url: {v}")
        return v
    
    @field_validator('username', 'password')
    @classmethod
    def validate_credentials(cls, v: str) -> str:
        """Validate credentials are non-empty."""
        if not v or v.strip() == "":
            raise ValueError("Grafana credentials (username, password) cannot be empty")
        return v


