"""End-to-end tests for user workflows."""

import pytest
from fastapi import status


@pytest.mark.e2e
@pytest.mark.slow
class TestUserWorkflows:
    """Test complete user workflows."""
    
    def test_user_registration_to_login_workflow(self, client):
        """Test complete workflow: register -> login -> access protected endpoint."""
        # Step 1: Register user
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "workflowuser",
                "email": "workflow@example.com",
                "password": "SecurePass123!@#"
            }
        )
        assert register_response.status_code == status.HTTP_200_OK
        user_data = register_response.json()
        assert user_data["username"] == "workflowuser"
        
        # Step 2: Login
        login_response = client.post(
            "/api/auth/token",
            data={
                "username": "workflowuser",
                "password": "SecurePass123!@#"
            }
        )
        assert login_response.status_code == status.HTTP_200_OK
        token_data = login_response.json()
        token = token_data["access_token"]
        
        # Step 3: Access protected endpoint
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == status.HTTP_200_OK
        me_data = me_response.json()
        assert me_data["username"] == "workflowuser"
    
    def test_user_service_access_workflow(self, client, db_session):
        """Test workflow: login -> check services -> access gateway."""
        # Create a service
        from app.models import Service
        service = Service(
            name="e2e-service",
            service_type="file_storage",
            base_url="http://e2e-service:8000",
            is_active=True
        )
        db_session.add(service)
        db_session.commit()
        
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "serviceuser",
                "email": "service@example.com",
                "password": "SecurePass123!@#"
            }
        )
        
        login_response = client.post(
            "/api/auth/token",
            data={
                "username": "serviceuser",
                "password": "SecurePass123!@#"
            }
        )
        token = login_response.json()["access_token"]
        
        # List services
        services_response = client.get(
            "/api/services",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert services_response.status_code == status.HTTP_200_OK
        services = services_response.json()
        assert len(services) >= 1
        
        # Check health
        health_response = client.get(
            "/api/health/services",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert health_response.status_code == status.HTTP_200_OK


@pytest.mark.e2e
@pytest.mark.slow
class TestAdminWorkflows:
    """Test complete admin workflows."""
    
    def test_admin_service_management_workflow(self, client, admin_token, db_session):
        """Test workflow: admin creates service -> updates -> deletes."""
        # Step 1: Create service
        create_response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "admin-service",
                "service_type": "file_storage",
                "base_url": "http://admin-service:8000",
                "api_url": "http://admin-service:8000/api",
                "health_check_url": "http://admin-service:8000/health",
                "requires_auth": True,
                "auth_token": "admin-token"
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        service_data = create_response.json()
        service_id = service_data["id"]
        
        # Step 2: Get service
        get_response = client.get(
            f"/api/services/{service_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == status.HTTP_200_OK
        
        # Step 3: Update service
        update_response = client.put(
            f"/api/services/{service_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "admin-service",
                "service_type": "media_server",
                "base_url": "http://admin-service-updated:8000",
                "requires_auth": False
            }
        )
        assert update_response.status_code == status.HTTP_200_OK
        updated_data = update_response.json()
        assert updated_data["service_type"] == "media_server"
        
        # Step 4: Delete service
        delete_response = client.delete(
            f"/api/services/{service_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        verify_response = client.get(
            f"/api/services/{service_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND
