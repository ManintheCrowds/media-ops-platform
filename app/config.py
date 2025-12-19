"""Configuration management for the platform."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Self-Hosted Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    
    # Database
    database_url: str = "postgresql://platform:platform@postgres:5432/platform"
    
    # Authentication
    jwt_secret_key: str = "change-me-in-production-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    oauth2_token_url: str = "/api/auth/token"
    
    # Service URLs
    seafile_url: Optional[str] = "http://seafile:8000"
    seafile_api_token: Optional[str] = None
    
    jellyfin_url: Optional[str] = "http://jellyfin:8096"
    jellyfin_api_key: Optional[str] = None
    
    gitea_url: Optional[str] = "http://gitea:3000"
    gitea_api_token: Optional[str] = None
    
    prometheus_url: Optional[str] = "http://prometheus:9090"
    grafana_url: Optional[str] = "http://grafana:3000"
    grafana_username: Optional[str] = "admin"
    grafana_password: Optional[str] = "admin"
    
    vaultwarden_url: Optional[str] = "http://vaultwarden:80"
    vaultwarden_admin_token: Optional[str] = None
    
    # CORS
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables (e.g., Docker service configs)


settings = Settings()


