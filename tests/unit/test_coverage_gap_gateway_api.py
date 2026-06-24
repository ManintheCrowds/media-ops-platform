"""Targeted unit tests for app.api.gateway endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.auth.oauth2 import get_current_user
from app.models import Service


@pytest.mark.unit
class TestGatewayAPI:
    """Cover gateway router endpoints with mocked service clients."""

    def test_file_storage_libraries_no_service(self, client, test_user):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.get("/api/gateway/file-storage/libraries")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_file_storage_libraries_success(self, client, test_user, db_session):
        db_session.add(
            Service(
                name="seafile",
                service_type="file_storage",
                base_url="http://seafile:8000",
                is_active=True,
            )
        )
        db_session.commit()

        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            mock_client = AsyncMock()
            mock_client.get_libraries = AsyncMock(return_value=[{"id": "lib1"}])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            with patch("app.api.gateway.SeafileClient", return_value=mock_client):
                response = client.get("/api/gateway/file-storage/libraries")
            assert response.status_code == 200
            assert response.json()["libraries"] == [{"id": "lib1"}]
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_media_libraries_success(self, client, test_user, db_session):
        db_session.add(
            Service(
                name="jellyfin",
                service_type="media_server",
                base_url="http://jellyfin:8096",
                is_active=True,
            )
        )
        db_session.commit()

        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            mock_client = AsyncMock()
            mock_client.get_libraries = AsyncMock(return_value=[{"Name": "Movies"}])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            with patch("app.api.gateway.JellyfinClient", return_value=mock_client):
                response = client.get("/api/gateway/media-server/libraries")
            assert response.status_code == 200
            assert "libraries" in response.json()
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_security_stats_requires_admin(self, client, test_user, db_session):
        db_session.add(
            Service(
                name="vaultwarden",
                service_type="security",
                base_url="http://vaultwarden:80",
                is_active=True,
            )
        )
        db_session.commit()

        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.get("/api/gateway/security/stats")
            assert response.status_code == 403
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_security_stats_success(self, client, test_admin_user, db_session):
        db_session.add(
            Service(
                name="vaultwarden",
                service_type="security",
                base_url="http://vaultwarden:80",
                is_active=True,
            )
        )
        db_session.commit()

        app.dependency_overrides[get_current_user] = lambda: test_admin_user
        try:
            mock_client = AsyncMock()
            mock_client.get_stats = AsyncMock(return_value={"users": 1})
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            with patch("app.api.gateway.VaultwardenClient", return_value=mock_client):
                response = client.get("/api/gateway/security/stats")
            assert response.status_code == 200
            assert response.json()["stats"]["users"] == 1
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_proxy_service_not_found(self, client, test_user):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.get("/api/gateway/proxy/missing-service/foo")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_proxy_path_traversal_blocked(self, client, test_user, db_session):
        db_session.add(
            Service(
                name="prometheus",
                service_type="monitoring",
                base_url="http://prometheus:9090",
                is_active=True,
            )
        )
        db_session.commit()

        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.get(
                "/api/gateway/proxy/prometheus/..%2F..%2Fetc%2Fpasswd"
            )
            assert response.status_code == 400
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_proxy_get_success(self, client, test_user, db_session):
        db_session.add(
            Service(
                name="grafana-svc",
                service_type="monitoring",
                base_url="http://grafana:3000",
                is_active=True,
            )
        )
        db_session.commit()

        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            mock_response = MagicMock()
            mock_response.content = b"ok"
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/plain"}
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            with patch("app.api.gateway.httpx.AsyncClient", return_value=mock_client):
                response = client.get("/api/gateway/proxy/grafana-svc/api/health")
            assert response.status_code == 200
            assert response.content == b"ok"
        finally:
            app.dependency_overrides.pop(get_current_user, None)
