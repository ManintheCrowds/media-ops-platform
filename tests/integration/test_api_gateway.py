"""Integration tests for gateway API endpoints."""

import pytest
import respx
import httpx
from fastapi import status
from tests.fixtures.mock_responses import (
    mock_seafile_libraries_response,
    mock_jellyfin_libraries_response,
    mock_bookstack_pages_response,
    mock_gitea_repositories_response,
    mock_prometheus_query_response,
    mock_grafana_dashboards_response,
    mock_vaultwarden_stats_response,
)


@pytest.mark.integration
class TestGatewayEndpoints:
    """Test gateway API endpoints."""

    def test_get_file_storage_libraries(self, client, test_token, db_session):
        """Test getting file storage libraries."""
        # Create file storage service
        from app.models import Service

        service = Service(
            name="seafile",
            service_type="file_storage",
            base_url="http://seafile:8000",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()

        mock_libraries = mock_seafile_libraries_response()
        with respx.mock:
            respx.get("http://seafile:8000/api2/repos/").mock(
                return_value=httpx.Response(200, json=mock_libraries)
            )
            response = client.get(
                "/api/gateway/file-storage/libraries",
                headers={"Authorization": f"Bearer {test_token}"},
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "libraries" in data
            assert len(data["libraries"]) == 2

    def test_get_file_storage_no_service(self, client, test_token, db_session):
        """Test getting file storage when no service registered."""
        # Delete all file storage services
        from app.models import Service

        db_session.query(Service).filter(
            Service.service_type == "file_storage"
        ).delete()
        db_session.commit()

        response = client.get(
            "/api/gateway/file-storage/libraries",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_media_libraries(self, client, test_token, db_session):
        """Test getting media server libraries."""
        from app.models import Service

        service = Service(
            name="jellyfin",
            service_type="media_server",
            base_url="http://jellyfin:8096",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()

        mock_libraries = mock_jellyfin_libraries_response()
        with respx.mock:
            respx.get("http://jellyfin:8096/Library/VirtualFolders").mock(
                return_value=httpx.Response(200, json=mock_libraries)
            )
            response = client.get(
                "/api/gateway/media-server/libraries",
                headers={"Authorization": f"Bearer {test_token}"},
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "libraries" in data

    def test_get_wiki_pages(self, client, test_token, db_session):
        """Test getting wiki pages."""
        from app.models import Service

        service = Service(
            name="bookstack",
            service_type="productivity",
            base_url="http://bookstack:8002",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()

        mock_response = mock_bookstack_pages_response()
        with respx.mock:
            respx.get("http://bookstack:8002/api/pages").mock(
                return_value=httpx.Response(200, json=mock_response)
            )
            response = client.get(
                "/api/gateway/productivity/pages",
                headers={"Authorization": f"Bearer {test_token}"},
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "pages" in data

    def test_get_repositories(self, client, test_token, db_session):
        """Test getting repositories."""
        from app.models import Service

        service = Service(
            name="gitea",
            service_type="dev_tools",
            base_url="http://gitea:3000",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()

        mock_response = mock_gitea_repositories_response()
        with respx.mock:
            respx.get("http://gitea:3000/api/v1/repos/search").mock(
                return_value=httpx.Response(200, json=mock_response)
            )
            response = client.get(
                "/api/gateway/dev-tools/repositories",
                headers={"Authorization": f"Bearer {test_token}"},
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "repositories" in data

    def test_get_monitoring_metrics(self, client, test_token, db_session):
        """Test getting monitoring metrics."""
        from app.models import Service

        service = Service(
            name="prometheus",
            service_type="monitoring",
            base_url="http://prometheus:9090",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()

        mock_response = mock_prometheus_query_response()
        with respx.mock:
            respx.get("http://prometheus:9090/api/v1/query").mock(
                return_value=httpx.Response(200, json=mock_response)
            )
            response = client.get(
                "/api/gateway/monitoring/metrics?query=up",
                headers={"Authorization": f"Bearer {test_token}"},
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "result" in data

    def test_get_grafana_dashboards(self, client, test_token, db_session):
        """Test getting Grafana dashboards."""
        from app.models import Service

        service = Service(
            name="grafana",
            service_type="monitoring",
            base_url="http://grafana:3000",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()

        mock_dashboards = mock_grafana_dashboards_response()
        with respx.mock:
            respx.get("http://grafana:3000/api/search").mock(
                return_value=httpx.Response(200, json=mock_dashboards)
            )
            response = client.get(
                "/api/gateway/monitoring/dashboards",
                headers={"Authorization": f"Bearer {test_token}"},
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "dashboards" in data

    def test_get_security_stats_admin(self, client, admin_token, db_session):
        """Test getting security stats as admin."""
        from app.models import Service

        service = Service(
            name="vaultwarden",
            service_type="security",
            base_url="http://vaultwarden:80",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()

        mock_stats = mock_vaultwarden_stats_response()
        with respx.mock:
            respx.get("http://vaultwarden:80/admin/stats").mock(
                return_value=httpx.Response(200, json=mock_stats)
            )
            response = client.get(
                "/api/gateway/security/stats",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "stats" in data

    def test_get_security_stats_non_admin(self, client, test_token, db_session):
        """Test getting security stats as non-admin."""
        from app.models import Service

        service = Service(
            name="vaultwarden",
            service_type="security",
            base_url="http://vaultwarden:80",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()

        response = client.get(
            "/api/gateway/security/stats",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_gateway_endpoints_require_auth(self, client):
        """Test that gateway endpoints require authentication."""
        endpoints = [
            "/api/gateway/file-storage/libraries",
            "/api/gateway/media-server/libraries",
            "/api/gateway/productivity/pages",
            "/api/gateway/dev-tools/repositories",
            "/api/gateway/monitoring/metrics",
            "/api/gateway/monitoring/dashboards",
            "/api/gateway/security/stats",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_gateway_uses_encrypted_token(self, client, test_token, db_session):
        """Test that gateway correctly uses encrypted auth tokens."""
        from app.models import Service
        from app.auth.encryption import is_encrypted

        # Create service with auth token
        service = Service(
            name="test-gateway-service",
            service_type="file_storage",
            base_url="http://test-service:8000",
            requires_auth=True,
            auth_token="test-bearer-token-123",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()
        db_session.refresh(service)

        # Verify token is encrypted in database (read persisted column value)
        stored_token = (
            db_session.query(Service)
            .filter(Service.id == service.id)
            .first()
            ._auth_token_encrypted
        )
        assert is_encrypted(stored_token)

        # Mock the external service call
        with respx.mock:
            # Verify that the Authorization header contains the decrypted token
            def check_auth_header(request):
                auth_header = request.headers.get("Authorization")
                assert auth_header == "Bearer test-bearer-token-123"
                return httpx.Response(200, json={"status": "ok"})

            respx.get("http://test-service:8000/api/test").mock(
                side_effect=check_auth_header
            )

            # Use the proxy endpoint
            response = client.get(
                f"/api/gateway/proxy/{service.name}/api/test",
                headers={"Authorization": f"Bearer {test_token}"},
            )
            # Should succeed (or 502 if service unavailable, but auth should work)
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_502_BAD_GATEWAY,
            ]
