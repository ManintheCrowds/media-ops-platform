"""Unit tests for best-effort audit emission."""

from unittest.mock import MagicMock, patch

from app.utils.audit_emit import emit_audit_event


def test_emit_audit_posts_payload():
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.text = ""

    with patch("app.utils.audit_emit.settings") as mock_settings, patch(
        "app.utils.audit_emit.httpx.Client"
    ) as mock_client_cls:
        mock_settings.security_service_url = "http://security-service:8001"
        mock_settings.security_audit_timeout_seconds = 1.0
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = False
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        emit_audit_event(
            "auth.login",
            "login",
            success=True,
            username="alice",
            ip_address="127.0.0.1",
        )

        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == "http://security-service:8001/api/security/audit"
        assert kwargs["json"]["event_type"] == "auth.login"
        assert kwargs["json"]["success"] is True


def test_emit_audit_swallows_errors():
    with patch("app.utils.audit_emit.settings") as mock_settings, patch(
        "app.utils.audit_emit.httpx.Client",
        side_effect=ConnectionError("down"),
    ):
        mock_settings.security_service_url = "http://security-service:8001"
        mock_settings.security_audit_timeout_seconds = 1.0
        emit_audit_event("auth.fail", "login", success=False, username="bob")
