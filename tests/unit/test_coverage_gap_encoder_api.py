"""Targeted unit tests for app.api.encoder endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status

from app.main import app
from app.auth.oauth2 import get_current_user
from app.models.encoder.encoder_models import VideoEncoder
from app.models.encoder.enums import EncoderStatus
from app.exceptions import EncoderError


@pytest.mark.unit
class TestEncoderAPI:
    """Cover encoder router endpoints with mocked VideoEncoderService."""

    def test_list_encoders_empty(self, client, test_user):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            with patch("app.api.encoder.VideoEncoderService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.list_encoders = AsyncMock(return_value=[])
                mock_cls.return_value = mock_svc
                response = client.get("/api/encoder/encoders")
            assert response.status_code == 200
            assert response.json() == []
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_get_encoder_not_found(self, client, test_user):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            with patch("app.api.encoder.VideoEncoderService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.get_encoder = AsyncMock(
                    side_effect=EncoderError(
                        "Encoder not found",
                        status_code=status.HTTP_404_NOT_FOUND,
                    )
                )
                mock_cls.return_value = mock_svc
                response = client.get("/api/encoder/encoders/999")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_discover_encoders_requires_admin(self, client, test_user):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.post("/api/encoder/encoders/discover")
            assert response.status_code == 403
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_discover_encoders_success(self, client, test_admin_user):
        app.dependency_overrides[get_current_user] = lambda: test_admin_user
        try:
            with patch("app.api.encoder.VideoEncoderService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.discover_encoders = AsyncMock(return_value=[{"ip": "192.168.1.10"}])
                mock_cls.return_value = mock_svc
                response = client.post("/api/encoder/encoders/discover")
            assert response.status_code == 200
            data = response.json()
            assert data["discovered"] == [{"ip": "192.168.1.10"}]
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_register_encoder_requires_admin(self, client, test_user):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.post(
                "/api/encoder/encoders",
                json={"name": "enc1", "ip_address": "192.168.1.20"},
            )
            assert response.status_code == 403
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_get_encoder_status(self, client, test_user, db_session):
        encoder = VideoEncoder(
            name="Lab Encoder",
            ip_address="192.168.1.50",
            port=8080,
            status=EncoderStatus.ONLINE,
        )
        db_session.add(encoder)
        db_session.commit()
        db_session.refresh(encoder)

        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            with patch("app.api.encoder.VideoEncoderService") as mock_cls:
                mock_svc = AsyncMock()
                mock_svc.get_encoder_status = AsyncMock(
                    return_value={"encoder_id": encoder.id, "status": "online"}
                )
                mock_cls.return_value = mock_svc
                response = client.get(f"/api/encoder/encoders/{encoder.id}/status")
            assert response.status_code == 200
            assert response.json()["status"] == "online"
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_start_recording_requires_admin(self, client, test_user):
        app.dependency_overrides[get_current_user] = lambda: test_user
        try:
            response = client.post(
                "/api/encoder/encoders/1/record",
                json={"source_url": "rtsp://cam/stream"},
            )
            assert response.status_code == 403
        finally:
            app.dependency_overrides.pop(get_current_user, None)
