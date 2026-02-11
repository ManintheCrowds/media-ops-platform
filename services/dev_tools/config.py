"""Configuration for development tools services."""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from urllib.parse import urlparse
from app.config_base import BaseServiceConfig


class GiteaConfig(BaseServiceConfig):
    """Gitea configuration."""
    
    base_url: str = "http://gitea:3000"
    api_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    class Config:
        env_prefix = "GITEA_"
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
    
    @field_validator('api_token', 'username', 'password')
    @classmethod
    def validate_credentials(cls, v: Optional[str]) -> Optional[str]:
        """Validate credentials are non-empty if provided."""
        return BaseServiceConfig.validate_non_empty_string(v, "gitea_credentials")


