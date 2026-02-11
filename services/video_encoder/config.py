"""Configuration for video encoder services."""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from pathlib import Path
import ipaddress
from app.config_base import BaseServiceConfig


class EncoderConfig(BaseServiceConfig):
    """Video encoder service configuration."""
    
    encoder_storage_path: str = "/var/lib/platform/encoder_recordings"
    encoder_network_scan_range: str = "192.168.1.0/24"
    encoder_default_port: int = 80
    encoder_timeout: int = 30
    
    class Config:
        env_prefix = "ENCODER_"
        case_sensitive = False
    
    @field_validator('encoder_storage_path')
    @classmethod
    def validate_storage_path(cls, v: str) -> str:
        """Validate storage path exists or is creatable."""
        BaseServiceConfig.validate_path(v, must_be_creatable=True)
        return v
    
    @field_validator('encoder_network_scan_range')
    @classmethod
    def validate_network_range(cls, v: str) -> str:
        """Validate network scan range is a valid CIDR notation."""
        try:
            ipaddress.ip_network(v, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid network range format: {v} - {e}")
        return v
    
    @field_validator('encoder_default_port', 'encoder_timeout')
    @classmethod
    def validate_positive_int(cls, v: int) -> int:
        """Validate port and timeout are positive."""
        return BaseServiceConfig.validate_positive_int(v, "encoder_config")
    
    @property
    def storage_path(self) -> Path:
        """Get storage path as Path object."""
        return Path(self.encoder_storage_path)

