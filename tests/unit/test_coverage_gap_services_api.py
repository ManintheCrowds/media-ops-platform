"""Targeted tests for app.api.services endpoints."""

import pytest
from app.main import app
from app.auth.oauth2 import get_current_user
from app.models import Service


SERVICE_PAYLOAD = {
    "name": "test-svc",
    "service_type": "monitoring",
    "base_url": "http://prometheus:9090",
    "api_url": "http://prometheus:9090/api/v1",
    "health_check_url": "http://prometheus:9090/-/healthy",
    "requires_auth": False,
}


@pytest.mark.unit
class TestServicesAPI:
    """Cover service registration CRUD endpoints."""

    def test_list_services(self, client, test_user, db_session):
        service = Service(
            name="listed",
            service_type="monitoring",
            base_url="http://grafana:3000",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.get("/api/services/")
            assert response.status_code == 200
            names = [item["name"] for item in response.json()]
            assert "listed" in names
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_get_service_not_found(self, client, test_user):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.get("/api/services/9999")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_create_service_requires_admin(self, client, test_user):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.post("/api/services/", json=SERVICE_PAYLOAD)
            assert response.status_code == 403
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_create_service_success(self, client, test_admin_user):
        app.dependency_overrides[get_current_user] = lambda: test_admin_user
        try:
            response = client.post("/api/services/", json=SERVICE_PAYLOAD)
            assert response.status_code == 201
            assert response.json()["name"] == "test-svc"
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_create_service_duplicate_name(self, client, test_admin_user, db_session):
        db_session.add(
            Service(
                name="test-svc",
                service_type="monitoring",
                base_url="http://existing:9090",
                is_active=True,
            )
        )
        db_session.commit()
        app.dependency_overrides[get_current_user] = lambda: test_admin_user
        try:
            response = client.post("/api/services/", json=SERVICE_PAYLOAD)
            assert response.status_code == 400
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_create_service_invalid_url(self, client, test_admin_user):
        app.dependency_overrides[get_current_user] = lambda: test_admin_user
        bad_payload = {**SERVICE_PAYLOAD, "base_url": "http://169.254.169.254"}
        try:
            response = client.post("/api/services/", json=bad_payload)
            assert response.status_code == 400
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_update_service_success(self, client, test_admin_user, db_session):
        service = Service(
            name="upd-svc",
            service_type="monitoring",
            base_url="http://grafana:3000",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()
        db_session.refresh(service)
        app.dependency_overrides[get_current_user] = lambda: test_admin_user
        try:
            response = client.put(
                f"/api/services/{service.id}",
                json={**SERVICE_PAYLOAD, "name": "upd-svc"},
            )
            assert response.status_code == 200
            assert response.json()["api_url"] == SERVICE_PAYLOAD["api_url"]
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_delete_service_success(self, client, test_admin_user, db_session):
        service = Service(
            name="del-svc",
            service_type="monitoring",
            base_url="http://grafana:3000",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()
        db_session.refresh(service)
        app.dependency_overrides[get_current_user] = lambda: test_admin_user
        try:
            response = client.delete(f"/api/services/{service.id}")
            assert response.status_code == 204
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_delete_service_not_found(self, client, test_admin_user):
        app.dependency_overrides[get_current_user] = lambda: test_admin_user
        try:
            response = client.delete("/api/services/9999")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_current_user, None)
