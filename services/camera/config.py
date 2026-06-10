"""Configuration for camera services."""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from pathlib import Path
from app.config_base import BaseServiceConfig


class CameraConfig(BaseServiceConfig):
    """Camera service configuration."""
    
    # Arlo Configuration
    arlo_username: Optional[str] = None
    arlo_password: Optional[str] = None
    storage_path: str = "/var/lib/platform/camera_recordings"
    arlo_sync_interval: int = 300
    arlo_encryption_key: Optional[str] = None
    
    class Config:
        env_prefix = "ARLO_"
        case_sensitive = False
    
    @field_validator('storage_path')
    @classmethod
    def validate_storage_path(cls, v: str) -> str:
        """Validate storage path exists or is creatable."""
        BaseServiceConfig.validate_path(v, must_be_creatable=True)
        return v
    
    @field_validator('arlo_sync_interval')
    @classmethod
    def validate_sync_interval(cls, v: int) -> int:
        """Validate sync interval is positive."""
        return BaseServiceConfig.validate_positive_int(v, "arlo_sync_interval")
    
    @field_validator('arlo_username', 'arlo_password')
    @classmethod
    def validate_credentials(cls, v: Optional[str]) -> Optional[str]:
        """Validate credentials are non-empty if provided."""
        return BaseServiceConfig.validate_non_empty_string(v, "arlo_credentials")
    
    @property
    def path(self) -> Path:
        """Get storage path as Path object."""
        return Path(self.storage_path)

