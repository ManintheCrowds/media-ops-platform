"""Test data factories."""

from faker import Faker
from typing import Dict, Any

fake = Faker()


TEST_USER_PASSWORD = "SecurePass123!@#"


def create_user_data(**kwargs) -> Dict[str, Any]:
    """Create test user data."""
    defaults = {
        "username": fake.user_name(),
        "email": fake.email(),
        "password": TEST_USER_PASSWORD,
    }
    defaults.update(kwargs)
    return defaults


def create_service_data(**kwargs) -> Dict[str, Any]:
    """Create test service data."""
    defaults = {
        "name": fake.slug(),
        "service_type": "file_storage",
        "base_url": f"http://{fake.domain_name()}:8000",
        "api_url": f"http://{fake.domain_name()}:8000/api",
        "health_check_url": f"http://{fake.domain_name()}:8000/health",
        "requires_auth": True,
        "auth_token": fake.uuid4(),
    }
    defaults.update(kwargs)
    return defaults


def create_file_storage_service_data(**kwargs) -> Dict[str, Any]:
    """Create file storage service data."""
    return create_service_data(service_type="file_storage", name="seafile", **kwargs)


def create_media_server_service_data(**kwargs) -> Dict[str, Any]:
    """Create media server service data."""
    return create_service_data(service_type="media_server", name="jellyfin", **kwargs)


def create_productivity_service_data(**kwargs) -> Dict[str, Any]:
    """Create productivity service data."""
    return create_service_data(service_type="productivity", name="bookstack", **kwargs)


def create_dev_tools_service_data(**kwargs) -> Dict[str, Any]:
    """Create dev tools service data."""
    return create_service_data(service_type="dev_tools", name="gitea", **kwargs)


def create_monitoring_service_data(**kwargs) -> Dict[str, Any]:
    """Create monitoring service data."""
    return create_service_data(service_type="monitoring", name="prometheus", **kwargs)


def create_security_service_data(**kwargs) -> Dict[str, Any]:
    """Create security service data."""
    return create_service_data(service_type="security", name="vaultwarden", **kwargs)
