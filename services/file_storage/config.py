"""Configuration for file storage services."""

from pydantic_settings import BaseSettings
from typing import Optional


class SeafileConfig(BaseSettings):
    """Seafile configuration."""
    
    base_url: str = "http://seafile:8000"
    api_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    class Config:
        env_prefix = "SEAFILE_"
        case_sensitive = False


