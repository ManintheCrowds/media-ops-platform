"""Integration tests for database operations."""

import pytest
from app.models import User, Service
from app.auth.oauth2 import get_password_hash, verify_password
from datetime import datetime


@pytest.mark.integration
class TestDatabaseOperations:
    """Test database operations."""
    
    def test_user_crud_operations(self, db_session):
        """Test user CRUD operations."""
        # Create
        user = User(
            username="dbuser",
            email="dbuser@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_admin=False
        )
        db_session.add(user)
        db_session.commit()
        user_id = user.id
        
        # Read
        retrieved_user = db_session.query(User).filter(User.id == user_id).first()
        assert retrieved_user is not None
        assert retrieved_user.username == "dbuser"
        assert retrieved_user.email == "dbuser@example.com"
        
        # Update
        retrieved_user.email = "updated@example.com"
        db_session.commit()
        db_session.refresh(retrieved_user)
        assert retrieved_user.email == "updated@example.com"
        
        # Delete
        db_session.delete(retrieved_user)
        db_session.commit()
        
        deleted_user = db_session.query(User).filter(User.id == user_id).first()
        assert deleted_user is None
    
    def test_service_crud_operations(self, db_session):
        """Test service CRUD operations."""
        # Create
        service = Service(
            name="db-service",
            service_type="file_storage",
            base_url="http://db-service:8000",
            is_active=True
        )
        db_session.add(service)
        db_session.commit()
        service_id = service.id
        
        # Read
        retrieved_service = db_session.query(Service).filter(Service.id == service_id).first()
        assert retrieved_service is not None
        assert retrieved_service.name == "db-service"
        
        # Update
        retrieved_service.health_status = "healthy"
        retrieved_service.last_health_check = datetime.utcnow()
        db_session.commit()
        db_session.refresh(retrieved_service)
        assert retrieved_service.health_status == "healthy"
        assert retrieved_service.last_health_check is not None
        
        # Delete
        db_session.delete(retrieved_service)
        db_session.commit()
        
        deleted_service = db_session.query(Service).filter(Service.id == service_id).first()
        assert deleted_service is None
    
    def test_user_password_verification(self, db_session):
        """Test password verification with database."""
        password = "securepassword123"
        user = User(
            username="passworduser",
            email="password@example.com",
            hashed_password=get_password_hash(password),
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Verify password
        retrieved_user = db_session.query(User).filter(User.username == "passworduser").first()
        assert verify_password(password, retrieved_user.hashed_password) is True
        assert verify_password("wrongpassword", retrieved_user.hashed_password) is False
    
    def test_service_query_filters(self, db_session):
        """Test querying services with filters."""
        # Create multiple services
        services = [
            Service(name="service1", service_type="file_storage", base_url="http://s1:8000", is_active=True),
            Service(name="service2", service_type="media_server", base_url="http://s2:8000", is_active=True),
            Service(name="service3", service_type="file_storage", base_url="http://s3:8000", is_active=False),
        ]
        for service in services:
            db_session.add(service)
        db_session.commit()
        
        # Query active services
        active_services = db_session.query(Service).filter(Service.is_active == True).all()
        assert len(active_services) == 2
        
        # Query by service type
        file_storage = db_session.query(Service).filter(Service.service_type == "file_storage").all()
        assert len(file_storage) == 2
        
        # Query active file storage
        active_file_storage = db_session.query(Service).filter(
            Service.service_type == "file_storage",
            Service.is_active == True
        ).all()
        assert len(active_file_storage) == 1
    
    def test_user_query_filters(self, db_session):
        """Test querying users with filters."""
        # Create multiple users
        users = [
            User(username="user1", email="user1@example.com", hashed_password="hash1", is_active=True, is_admin=False),
            User(username="user2", email="user2@example.com", hashed_password="hash2", is_active=True, is_admin=True),
            User(username="user3", email="user3@example.com", hashed_password="hash3", is_active=False, is_admin=False),
        ]
        for user in users:
            db_session.add(user)
        db_session.commit()
        
        # Query active users
        active_users = db_session.query(User).filter(User.is_active == True).all()
        assert len(active_users) == 2
        
        # Query admin users
        admin_users = db_session.query(User).filter(User.is_admin == True).all()
        assert len(admin_users) == 1
        
        # Query by username
        user = db_session.query(User).filter(User.username == "user1").first()
        assert user is not None
        assert user.email == "user1@example.com"
    
    def test_service_health_status_updates(self, db_session):
        """Test updating service health status."""
        service = Service(
            name="health-service",
            service_type="monitoring",
            base_url="http://health:8000",
            health_status="unknown"
        )
        db_session.add(service)
        db_session.commit()
        
        # Update health status
        service.health_status = "healthy"
        service.last_health_check = datetime.utcnow()
        db_session.commit()
        db_session.refresh(service)
        
        assert service.health_status == "healthy"
        assert service.last_health_check is not None
        
        # Update to unhealthy
        service.health_status = "unhealthy"
        db_session.commit()
        db_session.refresh(service)
        
        assert service.health_status == "unhealthy"
    
    def test_user_service_relationships(self, db_session):
        """Test that users and services can coexist independently."""
        user = User(
            username="relationuser",
            email="relation@example.com",
            hashed_password=get_password_hash("password123")
        )
        service = Service(
            name="relationservice",
            service_type="file_storage",
            base_url="http://relation:8000"
        )
        
        db_session.add(user)
        db_session.add(service)
        db_session.commit()
        
        # Both should exist independently
        assert db_session.query(User).filter(User.username == "relationuser").first() is not None
        assert db_session.query(Service).filter(Service.name == "relationservice").first() is not None
