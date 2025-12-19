"""Configuration for security services."""

from pydantic_settings import BaseSettings
from typing import Optional


class VaultwardenConfig(BaseSettings):
    """Vaultwarden configuration."""
    
    base_url: str = "http://vaultwarden:80"
    admin_token: Optional[str] = None
    
    class Config:
        env_prefix = "VAULTWARDEN_"
        case_sensitive = False


