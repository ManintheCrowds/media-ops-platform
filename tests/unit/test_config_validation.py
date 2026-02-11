"""Unit tests for configuration validation and error handling."""

import pytest
import os
from pydantic import ValidationError

from app.config import Settings


def build_settings(**kwargs):
    """Create Settings without loading from .env for isolated tests."""
    return Settings.model_validate(kwargs)


@pytest.fixture(autouse=True)
def clear_required_env(monkeypatch):
    """Ensure required secrets are not injected from environment."""
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)


@pytest.mark.unit
class TestConfigRequiredFields:
    """Test required configuration fields."""
    
    def test_config_requires_secret_key(self):
        """Test that secret_key is required."""
        with pytest.raises(ValidationError) as exc_info:
            build_settings(
                jwt_secret_key="a" * 32
                # Missing secret_key
            )
        
        errors = exc_info.value.errors()
        assert errors
    
    def test_config_requires_jwt_secret_key(self):
        """Test that jwt_secret_key is required."""
        with pytest.raises(ValidationError) as exc_info:
            build_settings(
                secret_key="a" * 32
                # Missing jwt_secret_key
            )
        
        errors = exc_info.value.errors()
        assert errors
    
    def test_config_requires_both_secrets(self):
        """Test that both secret keys are required."""
        with pytest.raises(ValidationError):
            build_settings()  # Missing both


@pytest.mark.unit
class TestConfigFieldValidation:
    """Test field validation rules."""
    
    def test_secret_key_min_length(self):
        """Test that secret_key must be at least 32 characters."""
        with pytest.raises(ValidationError) as exc_info:
            build_settings(
                secret_key="short",
                jwt_secret_key="a" * 32
            )
        
        errors = exc_info.value.errors()
        secret_key_error = next(
            (e for e in errors if e['loc'] == ('secret_key',)),
            None
        )
        assert secret_key_error is not None
        assert 'min_length' in str(secret_key_error['type']).lower()
    
    def test_jwt_secret_key_min_length(self):
        """Test that jwt_secret_key must be at least 32 characters."""
        with pytest.raises(ValidationError) as exc_info:
            build_settings(
                secret_key="a" * 32,
                jwt_secret_key="short"
            )
        
        errors = exc_info.value.errors()
        jwt_error = next(
            (e for e in errors if e['loc'] == ('jwt_secret_key',)),
            None
        )
        assert jwt_error is not None
        assert 'min_length' in str(jwt_error['type']).lower()
    
    def test_secret_key_valid_length(self):
        """Test that secret_key with valid length passes."""
        settings = build_settings(
            secret_key="a" * 32,
            jwt_secret_key="b" * 32
        )
        
        assert len(settings.secret_key) == 32
        assert len(settings.jwt_secret_key) == 32
    
    def test_secret_key_longer_than_min(self):
        """Test that secret_key longer than minimum passes."""
        settings = build_settings(
            secret_key="a" * 64,
            jwt_secret_key="b" * 64
        )
        
        assert len(settings.secret_key) == 64
        assert len(settings.jwt_secret_key) == 64


@pytest.mark.unit
class TestConfigOptionalFields:
    """Test optional configuration fields."""
    
    def test_optional_fields_default_to_none(self):
        """Test that optional fields default to None or specified defaults."""
        settings = build_settings(
            secret_key="a" * 32,
            jwt_secret_key="b" * 32
        )
        
        # Optional service URLs
        assert settings.seafile_api_token is None
        assert settings.jellyfin_api_key is None
        assert settings.gitea_api_token is None
        assert settings.grafana_password is None
    
    def test_optional_fields_can_be_set(self):
        """Test that optional fields can be set."""
        settings = build_settings(
            secret_key="a" * 32,
            jwt_secret_key="b" * 32,
            seafile_api_token="test-token",
            jellyfin_api_key="test-key",
            grafana_password="test-password"
        )
        
        assert settings.seafile_api_token == "test-token"
        assert settings.jellyfin_api_key == "test-key"
        assert settings.grafana_password == "test-password"


@pytest.mark.unit
class TestConfigDefaults:
    """Test configuration default values."""
    
    def test_default_app_name(self):
        """Test default app name."""
        settings = build_settings(
            secret_key="a" * 32,
            jwt_secret_key="b" * 32
        )
        
        assert settings.app_name == "Self-Hosted Platform"
    
    def test_default_debug_false(self):
        """Test default debug is False."""
        settings = build_settings(
            secret_key="a" * 32,
            jwt_secret_key="b" * 32
        )
        
        assert settings.debug is False
    
    def test_default_database_url(self):
        """Test default database URL."""
        settings = build_settings(
            secret_key="a" * 32,
            jwt_secret_key="b" * 32
        )
        
        assert "postgresql://" in settings.database_url
        assert "platform" in settings.database_url
    
    def test_default_jwt_algorithm(self):
        """Test default JWT algorithm."""
        settings = build_settings(
            secret_key="a" * 32,
            jwt_secret_key="b" * 32
        )
        
        assert settings.jwt_algorithm == "HS256"
    
    def test_default_service_urls(self):
        """Test default service URLs."""
        settings = build_settings(
            secret_key="a" * 32,
            jwt_secret_key="b" * 32
        )
        
        assert settings.seafile_url == "http://seafile:8000"
        assert settings.jellyfin_url == "http://jellyfin:8096"
        assert settings.gitea_url == "http://gitea:3000"
        assert settings.prometheus_url == "http://prometheus:9090"
        assert settings.grafana_url == "http://grafana:3000"


@pytest.mark.unit
class TestConfigArloFields:
    """Test Arlo-specific configuration fields."""
    
    def test_arlo_fields_optional(self):
        """Test that Arlo fields are optional."""
        settings = build_settings(
            secret_key="a" * 32,
            jwt_secret_key="b" * 32
        )
        
        assert settings.arlo_username is None
        assert settings.arlo_password is None
    
    def test_arlo_fields_can_be_set(self):
        """Test that Arlo fields can be set."""
        settings = build_settings(
            secret_key="a" * 32,
            jwt_secret_key="b" * 32,
            arlo_username="test@example.com",
            arlo_password="testpass",
            arlo_storage_path="/custom/path"
        )
        
        assert settings.arlo_username == "test@example.com"
        assert settings.arlo_password == "testpass"
        assert settings.arlo_storage_path == "/custom/path"


@pytest.mark.unit
class TestConfigEncoderFields:
    """Test encoder-specific configuration fields."""
    
    def test_encoder_fields_have_defaults(self):
        """Test that encoder fields have defaults."""
        settings = build_settings(
            secret_key="a" * 32,
            jwt_secret_key="b" * 32
        )
        
        assert settings.encoder_storage_path == "/var/lib/platform/encoder_recordings"
        assert settings.encoder_network_scan_range == "192.168.1.0/24"
    
    def test_encoder_fields_can_be_overridden(self):
        """Test that encoder fields can be overridden."""
        settings = build_settings(
            secret_key="a" * 32,
            jwt_secret_key="b" * 32,
            encoder_storage_path="/custom/encoder/path",
            encoder_network_scan_range="10.0.0.0/24"
        )
        
        assert settings.encoder_storage_path == "/custom/encoder/path"
        assert settings.encoder_network_scan_range == "10.0.0.0/24"


@pytest.mark.unit
class TestConfigErrorHandling:
    """Test configuration error handling."""
    
    def test_invalid_database_url_format(self):
        """Test that invalid database URL format is handled."""
        # Pydantic will validate URL format if we add validators
        # For now, just test that it accepts string
        settings = Settings(
            secret_key="a" * 32,
            jwt_secret_key="b" * 32,
            database_url="invalid-url"
        )
        
        # Should still create settings (validation happens at connection time)
        assert settings.database_url == "invalid-url"
    
    def test_empty_string_secret_key(self):
        """Test that empty string secret_key fails validation."""
        with pytest.raises(ValidationError):
            Settings(
                secret_key="",
                jwt_secret_key="b" * 32
            )
    
    def test_none_secret_key(self):
        """Test that None secret_key fails validation."""
        with pytest.raises(ValidationError):
            Settings(
                secret_key=None,
                jwt_secret_key="b" * 32
            )

