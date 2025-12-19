"""Tests for configuration management."""

import pytest
import tempfile
import yaml
from pathlib import Path
from pi_client.config import Config


def test_config_load_defaults():
    """Test loading default configuration."""
    config = Config.load()
    
    assert config.device.device_id == ""
    assert config.api.base_url == ""
    assert config.display.port == 8080


def test_config_load_from_file():
    """Test loading configuration from file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            "device": {
                "device_id": "test-device",
                "device_name": "Test Device"
            },
            "api": {
                "base_url": "https://test.example.com"
            },
            "display": {
                "port": 9000
            }
        }
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        config = Config.load(config_path)
        
        assert config.device.device_id == "test-device"
        assert config.device.device_name == "Test Device"
        assert config.api.base_url == "https://test.example.com"
        assert config.display.port == 9000
    finally:
        Path(config_path).unlink()


def test_config_validate():
    """Test configuration validation."""
    config = Config()
    config.device.device_id = "test"
    config.api.base_url = "https://test.example.com"
    
    assert config.validate() is True
    
    # Missing device_id
    config.device.device_id = ""
    with pytest.raises(ValueError):
        config.validate()
