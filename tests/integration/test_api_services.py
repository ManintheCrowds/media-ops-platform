"""Integration tests for service management API endpoints."""

import pytest
from fastapi import status
from app.auth.encryption import is_encrypted


@pytest.mark.integration
class TestServiceEndpoints:
    """Test service management API endpoints."""
    
    def test_list_services(self, client, test_token, test_service):
        """Test listing services."""
        response = client.get(
            "/api/services",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(s["name"] == test_service.name for s in data)
    
    def test_list_services_no_auth(self, client):
        """Test listing services without authentication."""
        response = client.get("/api/services")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_service(self, client, test_token, test_service):
        """Test getting a specific service."""
        response = client.get(
            f"/api/services/{test_service.id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_service.id
        assert data["name"] == test_service.name
    
    def test_get_service_not_found(self, client, test_token):
        """Test getting non-existent service."""
        response = client.get(
            "/api/services/99999",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_create_service_admin(self, client, admin_token):
        """Test creating service as admin."""
        response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "new-service",
                "service_type": "file_storage",
                "base_url": "http://new-service:8000",
                "api_url": "http://new-service:8000/api",
                "health_check_url": "http://new-service:8000/health",
                "requires_auth": True,
                "auth_token": "test-token"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "new-service"
        assert data["service_type"] == "file_storage"
    
    def test_create_service_non_admin(self, client, test_token):
        """Test creating service as non-admin."""
        response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "name": "new-service",
                "service_type": "file_storage",
                "base_url": "http://new-service:8000"
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_service_duplicate_name(self, client, admin_token, test_service):
        """Test creating service with duplicate name."""
        response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": test_service.name,
                "service_type": "file_storage",
                "base_url": "http://different:8000"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_service_admin(self, client, admin_token, test_service):
        """Test updating service as admin."""
        response = client.put(
            f"/api/services/{test_service.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": test_service.name,
                "service_type": "media_server",
                "base_url": "http://updated:8000",
                "requires_auth": False
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service_type"] == "media_server"
        assert data["base_url"] == "http://updated:8000"
    
    def test_update_service_non_admin(self, client, test_token, test_service):
        """Test updating service as non-admin."""
        response = client.put(
            f"/api/services/{test_service.id}",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "name": test_service.name,
                "service_type": "file_storage",
                "base_url": "http://updated:8000"
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_service_admin(self, client, admin_token, db_session):
        """Test deleting service as admin."""
        # Create a service to delete
        from app.models import Service
        service = Service(
            name="to-delete",
            service_type="file_storage",
            base_url="http://delete:8000"
        )
        db_session.add(service)
        db_session.commit()
        service_id = service.id
        
        response = client.delete(
            f"/api/services/{service_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's deleted
        get_response = client.get(
            f"/api/services/{service_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_service_non_admin(self, client, test_token, test_service):
        """Test deleting service as non-admin."""
        response = client.delete(
            f"/api/services/{test_service.id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_service_encrypts_token(self, client, admin_token, db_session):
        """Test that auth_token is encrypted when creating service via API."""
        response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "encrypted-service",
                "service_type": "file_storage",
                "base_url": "http://encrypted:8000",
                "auth_token": "plain-text-token-123"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        service_id = data["id"]
        
        # Verify token is encrypted in database
        from app.models import Service
        service = db_session.query(Service).filter(Service.id == service_id).first()
        assert service is not None
        assert is_encrypted(service._auth_token_encrypted)
        assert service._auth_token_encrypted != "plain-text-token-123"
        # But should decrypt correctly when accessed
        assert service.auth_token == "plain-text-token-123"
    
    def test_update_service_encrypts_token(self, client, admin_token, test_service, db_session):
        """Test that auth_token is encrypted when updating service via API."""
        response = client.put(
            f"/api/services/{test_service.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": test_service.name,
                "service_type": test_service.service_type,
                "base_url": test_service.base_url,
                "auth_token": "updated-plain-token"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Verify token is encrypted in database
        db_session.refresh(test_service)
        assert is_encrypted(test_service._auth_token_encrypted)
        assert test_service._auth_token_encrypted != "updated-plain-token"
        assert test_service.auth_token == "updated-plain-token"
    
    def test_service_response_excludes_auth_token(self, client, admin_token, test_service):
        """Test that auth_token is not exposed in API responses."""
        response = client.get(
            f"/api/services/{test_service.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # ServiceResponse model should not include auth_token
        assert "auth_token" not in data
