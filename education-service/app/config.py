"""Configuration management for the educational service."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Educational System Service"
    app_version: str = "0.1.0"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    
    # Database
    database_url: str = "postgresql://education:password@education-db:5432/education"
    
    # Platform Integration
    platform_url: str = "http://platform:8000"
    jwt_secret_key: str = "change-me-in-production-jwt-secret"
    jwt_algorithm: str = "HS256"
    
    # Service URLs (for integrations)
    bookstack_url: Optional[str] = "http://bookstack:80"
    bookstack_api_id: Optional[str] = None
    bookstack_api_secret: Optional[str] = None
    
    gitea_url: Optional[str] = "http://gitea:3000"
    gitea_api_token: Optional[str] = None
    
    seafile_url: Optional[str] = "http://seafile:8000"
    seafile_api_token: Optional[str] = None
    
    jellyfin_url: Optional[str] = "http://jellyfin:8096"
    jellyfin_api_key: Optional[str] = None
    
    # CORS
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # Sync Package Settings
    sync_package_storage_path: str = "/app/storage/sync-packages"
    sync_package_expiry_hours: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()


