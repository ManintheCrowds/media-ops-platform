"""Configuration for media server services."""

from pydantic_settings import BaseSettings
from typing import Optional


class JellyfinConfig(BaseSettings):
    """Jellyfin configuration."""
    
    base_url: str = "http://jellyfin:8096"
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    class Config:
        env_prefix = "JELLYFIN_"
        case_sensitive = False


