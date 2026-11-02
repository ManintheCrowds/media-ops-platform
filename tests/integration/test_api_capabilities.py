"""Integration tests for capabilities and auth validate."""

import pytest
from fastapi import status


@pytest.mark.integration
class TestCapabilities:
    def test_capabilities_shape(self, client):
        response = client.get("/api/capabilities")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sync"]["protocol_version"] == "1"
        assert data["sync"]["education_base_path"] == "/api/v1/pi"
        assert data["sync"]["download_mode"] == "stream"
        assert data["auth"]["validate_path"] == "/api/auth/validate"
        assert "file_storage" in data["gateway"]["service_types"]


@pytest.mark.integration
@pytest.mark.auth
class TestAuthValidate:
    def test_validate_requires_token(self, client):
        response = client.get("/api/auth/validate")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_validate_with_token(self, client, test_token, test_user):
        response = client.get(
            "/api/auth/validate",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sub"] == test_user.username
        assert data["email"] == test_user.email
        assert "is_admin" in data
        assert data["is_active"] is True
