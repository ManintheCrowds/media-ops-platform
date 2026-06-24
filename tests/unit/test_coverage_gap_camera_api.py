"""Targeted unit tests for app.api.camera endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status

from app.main import app
from app.auth.oauth2 import get_current_user
from app.models.camera.arlo_models import ArloCamera, ArloBaseStation
from app.models.camera.enums import ArloStatus
from app.exceptions import ArloError


@pytest.mark.unit
class TestCameraAPI:
    """Cover camera router endpoints with mocked ArloService."""

    def test_list_cameras_empty(self, client, test_user):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            with patch("app.api.camera.ArloService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.list_cameras = AsyncMock(return_value=[])
                mock_cls.return_value = mock_svc
                response = client.get("/api/camera/cameras")
            assert response.status_code == 200
            assert response.json() == []
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_list_cameras_with_data(self, client, test_user, db_session):
        station = ArloBaseStation(name="Base", serial_number="BS001")
        db_session.add(station)
        db_session.flush()
        camera = ArloCamera(
            base_station_id=station.id,
            name="Front Door",
            device_id="DEV001",
            status=ArloStatus.ONLINE,
        )
        db_session.add(camera)
        db_session.commit()

        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.get("/api/camera/cameras")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Front Door"
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_get_camera_not_found(self, client, test_user):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            with patch("app.api.camera.ArloService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.get_camera = AsyncMock(
                    side_effect=ArloError(
                        "Camera not found",
                        status_code=status.HTTP_404_NOT_FOUND,
                    )
                )
                mock_cls.return_value = mock_svc
                response = client.get("/api/camera/cameras/999")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_discover_cameras_requires_admin(self, client, test_user):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.post("/api/camera/cameras/discover", json={})
            assert response.status_code == 403
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_discover_cameras_success(self, client, test_admin_user, db_session):
        station = ArloBaseStation(name="Base", serial_number="BS002")
        db_session.add(station)
        db_session.flush()
        discovered = ArloCamera(
            base_station_id=station.id,
            name="Discovered",
            device_id="DEV002",
            status=ArloStatus.ONLINE,
        )
        db_session.add(discovered)
        db_session.commit()
        db_session.refresh(discovered)
        discovered.created_at = None
        discovered.updated_at = None

        app.dependency_overrides[get_current_user] = lambda: test_admin_user
        try:
            with patch("app.api.camera.ArloService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.discover_cameras = AsyncMock(
                    return_value=[{"device_id": "DEV002", "name": "Discovered"}]
                )
                mock_svc.register_camera = AsyncMock(return_value=discovered)
                mock_cls.return_value = mock_svc
                response = client.post("/api/camera/cameras/discover", json={})
            assert response.status_code == 200
            assert len(response.json()) == 1
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_arm_camera_requires_admin(self, client, test_user):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.post("/api/camera/cameras/1/arm")
            assert response.status_code == 403
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_arm_camera_success(self, client, test_admin_user, db_session):
        station = ArloBaseStation(name="Base", serial_number="BS003")
        db_session.add(station)
        db_session.flush()
        camera = ArloCamera(
            base_station_id=station.id,
            name="Porch",
            device_id="DEV003",
            is_armed=True,
            status=ArloStatus.ONLINE,
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)
        camera.created_at = None
        camera.updated_at = None

        app.dependency_overrides[get_current_user] = lambda: test_admin_user
        try:
            with patch("app.api.camera.ArloService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.arm_camera = AsyncMock(return_value=camera)
                mock_cls.return_value = mock_svc
                response = client.post(f"/api/camera/cameras/{camera.id}/arm")
            assert response.status_code == 200
            assert response.json()["is_armed"] is True
        finally:
            app.dependency_overrides.pop(get_current_user, None)
