"""Configuration for productivity services."""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from urllib.parse import urlparse
from app.config_base import BaseServiceConfig


class WikiConfig(BaseServiceConfig):
    """Wiki configuration (BookStack)."""
    
    base_url: str = "http://bookstack:80"
    api_token: Optional[str] = None
    api_id: Optional[str] = None
    api_secret: Optional[str] = None
    
    class Config:
        env_prefix = "WIKI_"
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
    
    @field_validator('api_token', 'api_id', 'api_secret')
    @classmethod
    def validate_api_credentials(cls, v: Optional[str]) -> Optional[str]:
        """Validate API credentials are non-empty if provided."""
        return BaseServiceConfig.validate_non_empty_string(v, "api_credentials")


