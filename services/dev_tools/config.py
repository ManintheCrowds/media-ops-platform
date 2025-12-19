"""Configuration for development tools services."""

from pydantic_settings import BaseSettings
from typing import Optional


class GiteaConfig(BaseSettings):
    """Gitea configuration."""
    
    base_url: str = "http://gitea:3000"
    api_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    class Config:
        env_prefix = "GITEA_"
        case_sensitive = False


