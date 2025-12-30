"""Configuration for camera services."""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class CameraConfig(BaseSettings):
    """Camera service configuration."""
    
    # Arlo Configuration
    arlo_username: Optional[str] = None
    arlo_password: Optional[str] = None
    arlo_storage_path: str = "/var/lib/platform/camera_recordings"
    arlo_sync_interval: int = 300
    arlo_encryption_key: Optional[str] = None
    
    class Config:
        env_prefix = "ARLO_"
        case_sensitive = False
    
    @property
    def storage_path(self) -> Path:
        """Get storage path as Path object."""
        return Path(self.arlo_storage_path)

