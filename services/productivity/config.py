"""Configuration for productivity services."""

from pydantic_settings import BaseSettings
from typing import Optional


class WikiConfig(BaseSettings):
    """Wiki configuration (BookStack)."""
    
    base_url: str = "http://bookstack:80"
    api_token: Optional[str] = None
    api_id: Optional[str] = None
    api_secret: Optional[str] = None
    
    class Config:
        env_prefix = "WIKI_"
        case_sensitive = False


