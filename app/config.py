"""Configuration management for the platform."""

from pydantic_settings import BaseSettings
from pydantic import model_validator, Field, field_validator
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Self-Hosted Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    secret_key: str = Field(..., min_length=32, description="Application secret key (REQUIRED - must be at least 32 characters)")
    
    # Debug Endpoint Security
    enable_debug_endpoints: bool = False  # Explicit flag for debug endpoints (separate from FastAPI debug)
    debug_endpoint_allowed_ips: list[str] = []  # IP whitelist for debug endpoints
    debug_endpoint_require_admin: bool = True  # Require admin authentication even in debug mode
    
    # Database
    database_url: str = "postgresql://platform:platform@postgres:5432/platform"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_pre_ping: bool = True
    
    # Authentication
    jwt_secret_key: str = Field(..., min_length=32, description="JWT secret key (REQUIRED - must be at least 32 characters)")
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
    grafana_password: Optional[str] = None  # Must be set via environment variable
    
    vaultwarden_url: Optional[str] = "http://vaultwarden:80"
    vaultwarden_admin_token: Optional[str] = None
    
    # Camera Integration (Arlo)
    arlo_username: Optional[str] = None
    arlo_password: Optional[str] = None
    arlo_storage_path: str = "/var/lib/platform/camera_recordings"
    arlo_sync_interval: int = 300
    arlo_encryption_key: Optional[str] = None
    
    # Video Encoder (AJA HELO)
    encoder_storage_path: str = "/var/lib/platform/encoder_recordings"
    encoder_network_scan_range: str = "192.168.1.0/24"
    
    # Gateway Request Limits
    max_request_size_mb: float = 10.0  # Maximum request body size in megabytes
    service_timeouts: dict[str, float] = {
        "file_storage": 60.0,
        "media_server": 120.0,
        "productivity": 30.0,
        "dev_tools": 45.0,
        "monitoring": 30.0,
        "security": 30.0
    }  # Per-service-type timeout configuration in seconds
    
    # SSRF Protection
    ssrf_allowed_internal_patterns: list[str] = [
        "http://seafile:*",
        "http://jellyfin:*",
        "http://bookstack:*",
        "http://gitea:*",
        "http://prometheus:*",
        "http://grafana:*",
        "http://vaultwarden:*",
        "http://postgres:*",
        "http://platform:*"
    ]
    
    # CORS
    cors_origins: list[str] = []
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    @field_validator('secret_key', 'jwt_secret_key')
    @classmethod
    def validate_secret_length(cls, v: str) -> str:
        """Validate that secrets meet minimum length requirements."""
        if len(v) < 32:
            raise ValueError(
                f"Secret must be at least 32 characters long for security. "
                f"Current length: {len(v)} characters. "
                f"Generate a secure secret using: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return v
    
    @model_validator(mode='after')
    def validate_cors_config(self):
        """Validate CORS configuration to prevent credential exposure vulnerabilities."""
        if self.cors_allow_credentials:
            if "*" in self.cors_origins:
                raise ValueError(
                    "CORS configuration error: cors_allow_credentials cannot be True "
                    "when cors_origins contains '*'. This creates a CSRF vulnerability. "
                    "Specify explicit origins instead."
                )
            if not self.cors_origins:
                if not self.debug:
                    logger.warning(
                        "CORS configuration warning: cors_allow_credentials is True but "
                        "cors_origins is empty. This will block all cross-origin requests. "
                        "Configure CORS_ORIGINS environment variable with specific origins."
                    )
        return self
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables (e.g., Docker service configs)


settings = Settings()


