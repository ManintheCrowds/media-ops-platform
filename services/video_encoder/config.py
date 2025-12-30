"""Configuration for video encoder services."""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class EncoderConfig(BaseSettings):
    """Video encoder service configuration."""
    
    encoder_storage_path: str = "/var/lib/platform/encoder_recordings"
    encoder_network_scan_range: str = "192.168.1.0/24"
    encoder_default_port: int = 80
    encoder_timeout: int = 30
    
    class Config:
        env_prefix = "ENCODER_"
        case_sensitive = False
    
    @property
    def storage_path(self) -> Path:
        """Get storage path as Path object."""
        return Path(self.encoder_storage_path)

