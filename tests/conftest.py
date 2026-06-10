"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
import os
import tempfile
import uuid
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from httpx import AsyncClient
import respx
from faker import Faker

# Set required environment variables before importing app modules
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long-enough")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-32-chars-long-enough")
# Writable storage paths for CameraConfig/EncoderConfig validation on CI runners
_test_storage_root = os.path.join(tempfile.gettempdir(), "platform-test-storage")
os.makedirs(os.path.join(_test_storage_root, "camera_recordings"), exist_ok=True)
os.makedirs(os.path.join(_test_storage_root, "encoder_recordings"), exist_ok=True)
os.environ.setdefault(
    "ARLO_STORAGE_PATH", os.path.join(_test_storage_root, "camera_recordings")
)
os.environ.setdefault(
    "ENCODER_STORAGE_PATH", os.path.join(_test_storage_root, "encoder_recordings")
)
# Disable live HIBP checks in tests (SecurePassword123! is in the breach DB)
os.environ.setdefault("SECURITY_HIBP_ENABLE_PASSWORD_CHECK", "false")
os.environ.setdefault("SECURITY_HIBP_ENABLE_EMAIL_CHECK", "false")
# CORS: force explicit origins for tests (credentials + '*' fails validation)
os.environ["CORS_ORIGINS"] = '["http://localhost:3000","http://127.0.0.1:3000"]'
# Redirect coverage output to a temp path to avoid permission issues
os.environ.setdefault(
    "COVERAGE_FILE", os.path.join(tempfile.gettempdir(), f"coverage-{uuid.uuid4().hex}")
)

from app.main import app
from app.models import Base, User, Service
from app.config import settings
from app.auth.oauth2 import get_password_hash
from app.database import get_db
from app.auth.jwt_handler import create_access_token
from datetime import timedelta

fake = Faker()

# Test database URL (SQLite for speed)
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """Create a test database session."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db: Session) -> Session:
    """Get database session."""
    return test_db


@pytest.fixture
def override_get_db(test_db: Session):
    """Override get_db dependency for testing."""

    def _get_db():
        try:
            yield test_db
        finally:
            test_db.rollback()

    return _get_db


@pytest.fixture
def client(override_get_db) -> TestClient:
    """Create a test client."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin_user(db_session: Session) -> User:
    """Create a test admin user."""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_token(test_user: User) -> str:
    """Create a JWT token for test user."""
    return create_access_token(
        data={
            "sub": test_user.username,
            "email": test_user.email,
            "is_admin": test_user.is_admin,
        },
        expires_delta=timedelta(minutes=30),
    )


@pytest.fixture
def admin_token(test_admin_user: User) -> str:
    """Create a JWT token for admin user."""
    return create_access_token(
        data={
            "sub": test_admin_user.username,
            "email": test_admin_user.email,
            "is_admin": test_admin_user.is_admin,
        },
        expires_delta=timedelta(minutes=30),
    )


@pytest.fixture
def test_service(db_session: Session) -> Service:
    """Create a test service."""
    service = Service(
        name="test-service",
        service_type="file_storage",
        base_url="http://test-service:8000",
        api_url="http://test-service:8000/api",
        health_check_url="http://test-service:8000/health",
        is_active=True,
        requires_auth=True,
        auth_token="test-token-123",
        health_status="unknown",
    )
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)
    return service


@pytest.fixture
def mock_httpx():
    """Mock httpx for service client tests."""
    with respx.mock() as respx_mock:
        yield respx_mock


@pytest.fixture
def sample_service_data():
    """Sample service data for testing."""
    return {
        "name": "seafile",
        "service_type": "file_storage",
        "base_url": "http://seafile:8000",
        "api_url": "http://seafile:8000/api2",
        "health_check_url": "http://seafile:8000/api2/ping/",
        "requires_auth": True,
        "auth_token": "test-api-token",
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": fake.user_name(),
        "email": fake.email(),
        "password": "SecurePass123!@#",
    }
