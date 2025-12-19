"""End-to-end tests for gateway workflows."""

import pytest
import respx
import httpx
from fastapi import status


@pytest.mark.e2e
@pytest.mark.slow
class TestGatewayWorkflows:
    """Test complete gateway workflows."""
    
    def test_file_storage_workflow(self, client, test_token, db_session):
        """Test complete file storage workflow."""
        # Setup service
        from app.models import Service
        service = Service(
            name="seafile-e2e",
            service_type="file_storage",
            base_url="http://seafile:8000",
            is_active=True
        )
        db_session.add(service)
        db_session.commit()
        
        # Access libraries
        mock_libraries = [
            {"id": "lib1", "name": "Library 1"},
            {"id": "lib2", "name": "Library 2"}
        ]
        with respx.mock:
            respx.get("http://seafile:8000/api2/repos/").mock(
                return_value=httpx.Response(200, json=mock_libraries)
            )
            response = client.get(
                "/api/gateway/file-storage/libraries",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["libraries"]) == 2
    
    def test_media_server_workflow(self, client, test_token, db_session):
        """Test complete media server workflow."""
        from app.models import Service
        service = Service(
            name="jellyfin-e2e",
            service_type="media_server",
            base_url="http://jellyfin:8096",
            is_active=True
        )
        db_session.add(service)
        db_session.commit()
        
        # Get libraries
        mock_libraries = [{"Name": "Movies", "CollectionType": "movies"}]
        with respx.mock:
            respx.get("http://jellyfin:8096/Library/VirtualFolders").mock(
                return_value=httpx.Response(200, json=mock_libraries)
            )
            libraries_response = client.get(
                "/api/gateway/media-server/libraries",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            assert libraries_response.status_code == status.HTTP_200_OK
        
        # Get recent items
        mock_items = [{"Name": "Movie 1", "Type": "Movie"}]
        with respx.mock:
            respx.get("http://jellyfin:8096/Items/Latest").mock(
                return_value=httpx.Response(200, json=mock_items)
            )
            recent_response = client.get(
                "/api/gateway/media-server/recent?limit=10",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            assert recent_response.status_code == status.HTTP_200_OK
    
    def test_monitoring_workflow(self, client, test_token, db_session):
        """Test complete monitoring workflow."""
        from app.models import Service
        prometheus = Service(
            name="prometheus-e2e",
            service_type="monitoring",
            base_url="http://prometheus:9090",
            is_active=True
        )
        grafana = Service(
            name="grafana-e2e",
            service_type="monitoring",
            base_url="http://grafana:3000",
            is_active=True
        )
        db_session.add(prometheus)
        db_session.add(grafana)
        db_session.commit()
        
        # Query Prometheus
        mock_query = {"status": "success", "data": {"resultType": "vector", "result": []}}
        with respx.mock:
            respx.get("http://prometheus:9090/api/v1/query").mock(
                return_value=httpx.Response(200, json=mock_query)
            )
            metrics_response = client.get(
                "/api/gateway/monitoring/metrics?query=up",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            assert metrics_response.status_code == status.HTTP_200_OK
        
        # Get Grafana dashboards
        mock_dashboards = [{"uid": "dash1", "title": "Dashboard 1"}]
        with respx.mock:
            respx.get("http://grafana:3000/api/search").mock(
                return_value=httpx.Response(200, json=mock_dashboards)
            )
            dashboards_response = client.get(
                "/api/gateway/monitoring/dashboards",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            assert dashboards_response.status_code == status.HTTP_200_OK
