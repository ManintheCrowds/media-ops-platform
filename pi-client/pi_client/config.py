"""Configuration management for Pi client."""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class DisplayConfig:
    """Display configuration."""
    port: int = 8080
    rotation: str = "landscape"  # landscape, portrait
    fullscreen: bool = True
    mode: str = "kiosk"  # kiosk, interactive, presentation, dashboard


@dataclass
class HardwareConfig:
    """Hardware configuration."""
    gpio_enabled: bool = True
    camera_enabled: bool = False
    audio_enabled: bool = True


@dataclass
class SecurityConfig:
    """Security configuration."""
    cert_path: str = "/etc/pi-client/certs/device.pem"
    encryption_enabled: bool = True


@dataclass
class CacheConfig:
    """Cache configuration."""
    directory: str = "~/.pi-client/cache"
    max_size_mb: int = 5000
    ttl_hours: int = 168  # 7 days


@dataclass
class APIConfig:
    """API configuration."""
    base_url: str = ""
    auth_token: str = ""
    timeout: int = 30
    retry_attempts: int = 3


@dataclass
class DeviceConfig:
    """Device configuration."""
    device_id: str = ""
    device_name: str = ""
    organization_id: Optional[int] = None


@dataclass
class Config:
    """Main configuration class."""
    device: DeviceConfig = field(default_factory=DeviceConfig)
    api: APIConfig = field(default_factory=APIConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    sync_interval: int = 3600  # 1 hour in seconds

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from file, environment variables, or defaults."""
        config = cls()
        
        # Try to find config file
        if config_path:
            config_paths = [Path(config_path)]
        else:
            config_paths = [
                Path("/etc/pi-client/config.yaml"),
                Path.home() / ".pi-client" / "config.yaml",
                Path("config.yaml"),
            ]
        
        config_data = {}
        for path in config_paths:
            if path.exists():
                try:
                    with open(path, "r") as f:
                        config_data = yaml.safe_load(f) or {}
                    break
                except Exception:
                    continue
        
        # Load from environment variables (override file config)
        config.device.device_id = os.getenv("PI_DEVICE_ID", config_data.get("device", {}).get("device_id", ""))
        config.device.device_name = os.getenv("PI_DEVICE_NAME", config_data.get("device", {}).get("device_name", ""))
        config.api.base_url = os.getenv("PI_API_URL", config_data.get("api", {}).get("base_url", ""))
        config.api.auth_token = os.getenv("PI_AUTH_TOKEN", config_data.get("api", {}).get("auth_token", ""))
        config.cache.directory = os.getenv("PI_CACHE_DIR", config_data.get("cache", {}).get("directory", "~/.pi-client/cache"))
        config.cache.max_size_mb = int(os.getenv("PI_CACHE_SIZE_MB", config_data.get("cache", {}).get("max_size_mb", 5000)))
        config.display.port = int(os.getenv("PI_DISPLAY_PORT", config_data.get("display", {}).get("port", 8080)))
        config.display.rotation = os.getenv("PI_DISPLAY_ROTATION", config_data.get("display", {}).get("rotation", "landscape"))
        config.display.fullscreen = os.getenv("PI_DISPLAY_FULLSCREEN", "true").lower() == "true"
        config.display.mode = os.getenv("PI_DISPLAY_MODE", config_data.get("display", {}).get("mode", "kiosk"))
        config.hardware.gpio_enabled = os.getenv("PI_GPIO_ENABLED", "true").lower() == "true"
        config.hardware.camera_enabled = os.getenv("PI_CAMERA_ENABLED", "false").lower() == "true"
        config.hardware.audio_enabled = os.getenv("PI_AUDIO_ENABLED", "true").lower() == "true"
        config.security.cert_path = os.getenv("PI_CERT_PATH", config_data.get("security", {}).get("cert_path", "/etc/pi-client/certs/device.pem"))
        config.security.encryption_enabled = os.getenv("PI_ENCRYPTION_ENABLED", "true").lower() == "true"
        config.sync_interval = int(os.getenv("PI_SYNC_INTERVAL", config_data.get("sync_interval", 3600)))
        
        # Expand user home directory in paths
        config.cache.directory = os.path.expanduser(config.cache.directory)
        
        return config
    
    def save(self, config_path: str) -> None:
        """Save configuration to file."""
        config_dict = {
            "device": {
                "device_id": self.device.device_id,
                "device_name": self.device.device_name,
            },
            "api": {
                "base_url": self.api.base_url,
                "auth_token": self.api.auth_token,
                "timeout": self.api.timeout,
            },
            "cache": {
                "directory": self.cache.directory,
                "max_size_mb": self.cache.max_size_mb,
                "ttl_hours": self.cache.ttl_hours,
            },
            "display": {
                "port": self.display.port,
                "rotation": self.display.rotation,
                "fullscreen": self.display.fullscreen,
                "mode": self.display.mode,
            },
            "hardware": {
                "gpio_enabled": self.hardware.gpio_enabled,
                "camera_enabled": self.hardware.camera_enabled,
                "audio_enabled": self.hardware.audio_enabled,
            },
            "security": {
                "cert_path": self.security.cert_path,
                "encryption_enabled": self.security.encryption_enabled,
            },
            "sync_interval": self.sync_interval,
        }
        
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False)
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.device.device_id:
            raise ValueError("device_id is required")
        if not self.api.base_url:
            raise ValueError("api.base_url is required")
        return True







