"""End-to-end tests for service workflows."""

import pytest
import respx
import httpx
from fastapi import status


@pytest.mark.e2e
@pytest.mark.slow
class TestServiceWorkflows:
    """Test complete service workflows."""
    
    def test_service_registration_to_health_check_workflow(self, client, admin_token, db_session):
        """Test workflow: register service -> check health -> update status."""
        # Step 1: Register service
        create_response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "workflow-service",
                "service_type": "file_storage",
                "base_url": "http://workflow-service:8000",
                "health_check_url": "http://workflow-service:8000/health",
                "requires_auth": False
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        service_data = create_response.json()
        service_id = service_data["id"]
        
        # Step 2: Check health
        with respx.mock:
            respx.get("http://workflow-service:8000/health").mock(
                return_value=httpx.Response(200)
            )
            health_response = client.get(
                f"/api/health/services/{service_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert health_response.status_code == status.HTTP_200_OK
            health_data = health_response.json()
            assert health_data["status"] == "healthy"
        
        # Step 3: Verify status in database
        from app.models import Service
        service = db_session.query(Service).filter(Service.id == service_id).first()
        assert service.health_status == "healthy"
    
    def test_service_gateway_access_workflow(self, client, test_token, db_session):
        """Test workflow: service exists -> access via gateway."""
        # Create service
        from app.models import Service
        service = Service(
            name="gateway-service",
            service_type="file_storage",
            base_url="http://gateway-service:8000",
            is_active=True
        )
        db_session.add(service)
        db_session.commit()
        
        # Access via gateway
        mock_libraries = [{"id": "1", "name": "Test Library"}]
        with respx.mock:
            respx.get("http://gateway-service:8000/api2/repos/").mock(
                return_value=httpx.Response(200, json=mock_libraries)
            )
            gateway_response = client.get(
                "/api/gateway/file-storage/libraries",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            assert gateway_response.status_code == status.HTTP_200_OK
            data = gateway_response.json()
            assert "libraries" in data
