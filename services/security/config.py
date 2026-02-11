"""Configuration for security services."""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from urllib.parse import urlparse
from app.config_base import BaseServiceConfig


class VaultwardenConfig(BaseServiceConfig):
    """Vaultwarden configuration."""
    
    base_url: str = "http://vaultwarden:80"
    admin_token: Optional[str] = None
    
    class Config:
        env_prefix = "VAULTWARDEN_"
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
    
    @field_validator('admin_token')
    @classmethod
    def validate_admin_token(cls, v: Optional[str]) -> Optional[str]:
        """Validate admin token is non-empty if provided."""
        return BaseServiceConfig.validate_non_empty_string(v, "admin_token")


