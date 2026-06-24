"""Targeted tests for service config validators to improve coverage."""

import pytest
from unittest.mock import patch
from pydantic import ValidationError

from services.productivity.config import WikiConfig
from services.monitoring.config import GrafanaConfig
from services.dev_tools.config import GiteaConfig


@pytest.mark.unit
class TestServiceConfigValidators:
    """Cover validate_base_url and credential validators across service configs."""

    @pytest.mark.parametrize(
        "config_cls,kwargs",
        [
            (WikiConfig, {"base_url": "http://bookstack:80"}),
            (GrafanaConfig, {"base_url": "http://grafana:3000"}),
            (GiteaConfig, {"base_url": "http://gitea:3000"}),
        ],
    )
    def test_valid_base_url(self, config_cls, kwargs):
        config = config_cls(**kwargs)
        assert config.base_url == kwargs["base_url"]

    @pytest.mark.parametrize(
        "config_cls",
        [WikiConfig, GrafanaConfig, GiteaConfig],
    )
    def test_invalid_base_url_missing_scheme(self, config_cls):
        with pytest.raises(ValidationError):
            config_cls(base_url="not-a-url")

    @pytest.mark.parametrize(
        "config_cls",
        [WikiConfig, GrafanaConfig, GiteaConfig],
    )
    def test_invalid_base_url_missing_netloc(self, config_cls):
        with pytest.raises(ValidationError):
            config_cls(base_url="http://")

    @pytest.mark.parametrize(
        "config_cls,module_path",
        [
            (WikiConfig, "services.productivity.config.urlparse"),
            (GrafanaConfig, "services.monitoring.config.urlparse"),
            (GiteaConfig, "services.dev_tools.config.urlparse"),
        ],
    )
    def test_base_url_non_value_error_reraised(self, config_cls, module_path):
        with patch(module_path, side_effect=TypeError("parse failed")):
            with pytest.raises(ValidationError, match="Invalid URL format"):
                config_cls(base_url="http://example.com")

    def test_grafana_empty_username_rejected(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            GrafanaConfig(base_url="http://grafana:3000", username="  ")

    def test_grafana_empty_password_rejected(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            GrafanaConfig(base_url="http://grafana:3000", password="")
