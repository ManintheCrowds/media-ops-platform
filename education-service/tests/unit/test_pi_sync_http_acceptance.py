"""Docker-free HTTP acceptance for Pi sync contract (sqlite + TestClient)."""

from __future__ import annotations

import gzip
import io
import os
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault(
    "JWT_SECRET_KEY", "test-jwt-secret-key-32-chars-long-enough!!"
)
os.environ.setdefault("DATABASE_URL", "sqlite://")

import app.models  # noqa: F401 — register all tables
from app.auth.device_auth import create_device_token
from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models.organization import Organization
from app.models.pi_device import (
    DeviceType,
    PackageStatus,
    PackageType,
    PiDevice,
    PiSyncPackage,
)


@pytest.fixture()
def sync_client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.services.pi_service.settings.sync_package_storage_path",
        str(tmp_path / "pkgs"),
    )
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    org = Organization(name="Test Org", slug="test-org")
    session.add(org)
    session.commit()
    session.refresh(org)

    device = PiDevice(
        device_id="pi-1",
        device_name="Kiosk",
        device_type=DeviceType.KIOSK,
        organization_id=org.id,
    )
    other = PiDevice(
        device_id="pi-2",
        device_name="Other",
        device_type=DeviceType.KIOSK,
        organization_id=org.id,
    )
    session.add_all([device, other])
    session.commit()
    session.refresh(device)
    session.refresh(other)

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        yield client, session, device, other
    finally:
        app.dependency_overrides.clear()
        client.close()
        session.close()
        engine.dispose()


def _device_headers(device_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_device_token(device_id)}"}


def _human_headers() -> dict[str, str]:
    token = jwt.encode(
        {"sub": "alice", "is_admin": True},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_check_returns_401(sync_client):
    client, _session, _device, _other = sync_client
    response = client.get("/api/v1/pi/devices/pi-1/sync/check")
    assert response.status_code == 401


def test_human_jwt_rejected_on_sync_check(sync_client):
    client, _session, _device, _other = sync_client
    response = client.get(
        "/api/v1/pi/devices/pi-1/sync/check",
        headers=_human_headers(),
    )
    assert response.status_code == 403


def test_wrong_device_token_rejected(sync_client):
    client, _session, _device, _other = sync_client
    response = client.get(
        "/api/v1/pi/devices/pi-1/sync/check",
        headers=_device_headers("pi-2"),
    )
    assert response.status_code == 403


def test_pending_without_checksum_has_updates_false(sync_client):
    client, session, device, _other = sync_client
    pkg = PiSyncPackage(
        device_id=device.id,
        package_type=PackageType.FULL,
        content_ids=[],
        status=PackageStatus.PENDING,
        checksum=None,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    session.add(pkg)
    session.commit()

    response = client.get(
        "/api/v1/pi/devices/pi-1/sync/check",
        headers=_device_headers("pi-1"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["has_updates"] is False
    assert body["available_packages"] == []


def test_request_download_complete_happy_path(sync_client):
    client, _session, _device, _other = sync_client
    headers = _device_headers("pi-1")

    request = client.post(
        "/api/v1/pi/devices/pi-1/sync/request",
        headers=headers,
        params={"package_type": "full", "content_ids": [1, 2]},
    )
    assert request.status_code == 200
    package = request.json()
    assert package["status"] == "ready"
    assert package["checksum"]
    package_id = package["id"]

    check = client.get("/api/v1/pi/devices/pi-1/sync/check", headers=headers)
    assert check.status_code == 200
    check_body = check.json()
    assert check_body["has_updates"] is True
    assert len(check_body["available_packages"]) == 1

    download = client.get(
        f"/api/v1/pi/devices/pi-1/sync/packages/{package_id}/download",
        headers=headers,
    )
    assert download.status_code == 200
    assert download.headers.get("content-type", "").startswith("application/gzip")
    assert download.headers.get("x-package-checksum") == package["checksum"]
    assert len(download.content) > 0
    # Valid gzip stream
    with gzip.GzipFile(fileobj=io.BytesIO(download.content)) as gz:
        gz.read()

    complete = client.post(
        "/api/v1/pi/devices/pi-1/sync/complete",
        headers=headers,
        json={"package_id": package_id},
    )
    assert complete.status_code == 200
    assert complete.json() == {"status": "completed", "package_id": package_id}


def test_download_pending_returns_accepted(sync_client):
    client, session, device, _other = sync_client
    pkg = PiSyncPackage(
        device_id=device.id,
        package_type=PackageType.FULL,
        content_ids=[],
        status=PackageStatus.PENDING,
        checksum=None,
        package_path=None,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    session.add(pkg)
    session.commit()
    session.refresh(pkg)

    response = client.get(
        f"/api/v1/pi/devices/pi-1/sync/packages/{pkg.id}/download",
        headers=_device_headers("pi-1"),
    )
    assert response.status_code == 202
