"""Unit tests for Pi sync package FSM (sqlite in-memory)."""

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-32-chars-long-enough!!")

import app.models  # noqa: F401 — register all tables
from app.database import Base
from app.models.organization import Organization
from app.models.pi_device import (
    DeviceType,
    PackageStatus,
    PackageType,
    PiDevice,
    PiSyncPackage,
)
from app.services.pi_service import PiSyncService


@pytest.fixture()
def db(tmp_path, monkeypatch):
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
    session.add(device)
    session.commit()
    session.refresh(device)
    try:
        yield session, device
    finally:
        session.close()
        engine.dispose()


def test_pending_without_checksum_not_in_has_updates(db):
    session, device = db
    from datetime import datetime, timedelta, timezone

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

    result = PiSyncService.check_for_updates(session, "pi-1")
    assert result["has_updates"] is False
    assert result["available_packages"] == []


def test_request_materializes_ready_package(db):
    session, _device = db
    package = PiSyncService.request_sync_package(
        session, "pi-1", PackageType.FULL, content_ids=[1, 2]
    )
    assert package.status == PackageStatus.READY
    assert package.checksum
    assert package.package_path
    assert Path(package.package_path).is_file()

    result = PiSyncService.check_for_updates(session, "pi-1")
    assert result["has_updates"] is True
    assert len(result["available_packages"]) == 1


def test_device_token_roundtrip():
    from jose import jwt

    from app.auth.device_auth import create_device_token, decode_device_token
    from app.config import settings

    token = create_device_token("pi-1", expires_minutes=60)
    principal = decode_device_token(token)
    assert principal is not None
    assert principal.device_id == "pi-1"

    human = jwt.encode(
        {"sub": "alice", "is_admin": True},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    assert decode_device_token(human) is None
