"""Targeted tests for app.api.health endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from app.main import app
from app.auth.oauth2 import get_current_user
from app.models import Service


@pytest.mark.unit
class TestHealthAPI:
    """Cover health router endpoints."""

    def test_basic_health_check(self, client):
        response = client.get("/api/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_check_all_services_empty(self, client, test_user, db_session):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.get("/api/health/services")
            assert response.status_code == 200
            data = response.json()
            assert data["services"] == {}
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_check_all_services_with_registered_service(self, client, test_user, db_session):
        service = Service(
            name="prometheus",
            service_type="monitoring",
            base_url="http://prometheus:9090",
            health_check_url="http://prometheus:9090/-/healthy",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.05

        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            with patch("app.api.health.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_cls.return_value = mock_client
                response = client.get("/api/health/services")
            assert response.status_code == 200
            data = response.json()
            assert data["services"]["prometheus"]["status"] == "healthy"
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_check_service_not_found(self, client, test_user):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.get("/api/health/services/9999")
            assert response.status_code == 200
            assert response.json()["status"] == "not_found"
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_check_service_success(self, client, test_user, db_session):
        service = Service(
            name="grafana",
            service_type="monitoring",
            base_url="http://grafana:3000",
            health_check_url="http://grafana:3000/api/health",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()
        db_session.refresh(service)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.02

        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            with patch("app.api.health.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_cls.return_value = mock_client
                response = client.get(f"/api/health/services/{service.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "grafana"
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_check_service_request_failure(self, client, test_user, db_session):
        service = Service(
            name="down",
            service_type="monitoring",
            base_url="http://down:9999",
            is_active=True,
        )
        db_session.add(service)
        db_session.commit()
        db_session.refresh(service)

        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            with patch("app.api.health.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(side_effect=Exception("connection refused"))
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_cls.return_value = mock_client
                response = client.get(f"/api/health/services/{service.id}")
            assert response.status_code == 200
            assert response.json()["status"] == "unhealthy"
        finally:
            app.dependency_overrides.pop(get_current_user, None)
