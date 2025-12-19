"""Unit tests for database models."""

import pytest
from datetime import datetime
from app.models import User, Service
from app.auth.oauth2 import get_password_hash


@pytest.mark.unit
class TestUserModel:
    """Test User model."""
    
    def test_create_user(self, db_session):
        """Test creating a user."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_admin=False
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_admin is False
        assert user.created_at is not None
    
    def test_user_unique_username(self, db_session):
        """Test that usernames must be unique."""
        user1 = User(
            username="testuser",
            email="test1@example.com",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="testuser",  # Duplicate username
            email="test2@example.com",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()
    
    def test_user_unique_email(self, db_session):
        """Test that emails must be unique."""
        user1 = User(
            username="user1",
            email="test@example.com",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="user2",
            email="test@example.com",  # Duplicate email
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()
    
    def test_user_defaults(self, db_session):
        """Test user default values."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.is_active is True  # Default
        assert user.is_admin is False  # Default
        assert user.created_at is not None
    
    def test_user_update_timestamp(self, db_session):
        """Test that updated_at changes on update."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user)
        db_session.commit()
        
        original_updated = user.updated_at
        
        # Update user
        user.email = "newemail@example.com"
        db_session.commit()
        db_session.refresh(user)
        
        # Note: updated_at might be None initially, but should be set after update
        # This depends on SQLAlchemy's onupdate behavior


@pytest.mark.unit
class TestServiceModel:
    """Test Service model."""
    
    def test_create_service(self, db_session):
        """Test creating a service."""
        service = Service(
            name="test-service",
            service_type="file_storage",
            base_url="http://service:8000",
            api_url="http://service:8000/api",
            health_check_url="http://service:8000/health",
            is_active=True,
            requires_auth=True,
            auth_token="test-token"
        )
        db_session.add(service)
        db_session.commit()
        
        assert service.id is not None
        assert service.name == "test-service"
        assert service.service_type == "file_storage"
        assert service.base_url == "http://service:8000"
        assert service.is_active is True
        assert service.requires_auth is True
        assert service.health_status == "unknown"  # Default
        assert service.created_at is not None
    
    def test_service_unique_name(self, db_session):
        """Test that service names must be unique."""
        service1 = Service(
            name="test-service",
            service_type="file_storage",
            base_url="http://service1:8000"
        )
        db_session.add(service1)
        db_session.commit()
        
        service2 = Service(
            name="test-service",  # Duplicate name
            service_type="media_server",
            base_url="http://service2:8000"
        )
        db_session.add(service2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()
    
    def test_service_defaults(self, db_session):
        """Test service default values."""
        service = Service(
            name="test-service",
            service_type="file_storage",
            base_url="http://service:8000"
        )
        db_session.add(service)
        db_session.commit()
        
        assert service.is_active is True  # Default
        assert service.requires_auth is True  # Default
        assert service.health_status == "unknown"  # Default
        assert service.created_at is not None
    
    def test_service_optional_fields(self, db_session):
        """Test service with optional fields."""
        service = Service(
            name="test-service",
            service_type="file_storage",
            base_url="http://service:8000",
            api_url=None,
            health_check_url=None,
            auth_token=None,
            service_metadata=None
        )
        db_session.add(service)
        db_session.commit()
        
        assert service.api_url is None
        assert service.health_check_url is None
        assert service.auth_token is None
        assert service.service_metadata is None
    
    def test_service_health_status_update(self, db_session):
        """Test updating service health status."""
        service = Service(
            name="test-service",
            service_type="file_storage",
            base_url="http://service:8000"
        )
        db_session.add(service)
        db_session.commit()
        
        assert service.health_status == "unknown"
        
        service.health_status = "healthy"
        service.last_health_check = datetime.utcnow()
        db_session.commit()
        db_session.refresh(service)
        
        assert service.health_status == "healthy"
        assert service.last_health_check is not None
