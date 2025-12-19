"""Integration tests for health check API endpoints."""

import pytest
import respx
import httpx
from fastapi import status


@pytest.mark.integration
class TestHealthEndpoints:
    """Test health check API endpoints."""
    
    def test_basic_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_check_all_services(self, client, test_token, test_service):
        """Test checking all services health."""
        with respx.mock:
            respx.get(test_service.health_check_url or f"{test_service.base_url}/health").mock(
                return_value=httpx.Response(200)
            )
            response = client.get(
                "/api/health/services",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "timestamp" in data
            assert "services" in data
            assert isinstance(data["services"], dict)
    
    def test_check_all_services_no_auth(self, client):
        """Test checking services without authentication."""
        response = client.get("/api/health/services")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_check_all_services_empty(self, client, test_token, db_session):
        """Test checking services when none are registered."""
        # Delete all services
        from app.models import Service
        db_session.query(Service).delete()
        db_session.commit()
        
        response = client.get(
            "/api/health/services",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["services"] == {}
    
    def test_check_specific_service(self, client, test_token, test_service):
        """Test checking specific service health."""
        with respx.mock:
            respx.get(test_service.health_check_url or f"{test_service.base_url}/health").mock(
                return_value=httpx.Response(200)
            )
            response = client.get(
                f"/api/health/services/{test_service.id}",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["service"] == test_service.name
            assert data["status"] in ["healthy", "unhealthy"]
            assert "timestamp" in data
    
    def test_check_service_not_found(self, client, test_token):
        """Test checking non-existent service."""
        response = client.get(
            "/api/health/services/99999",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "not_found"
    
    def test_check_service_unhealthy(self, client, test_token, test_service):
        """Test checking unhealthy service."""
        with respx.mock:
            respx.get(test_service.health_check_url or f"{test_service.base_url}/health").mock(
                return_value=httpx.Response(500)
            )
            response = client.get(
                f"/api/health/services/{test_service.id}",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "unhealthy"
    
    def test_check_service_timeout(self, client, test_token, test_service):
        """Test checking service that times out."""
        with respx.mock:
            respx.get(test_service.health_check_url or f"{test_service.base_url}/health").mock(
                side_effect=httpx.TimeoutException("Timeout")
            )
            response = client.get(
                f"/api/health/services/{test_service.id}",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "error" in data
