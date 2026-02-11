"""Unit tests for OAuth2 authentication."""

import pytest
from fastapi import status
from app.auth.oauth2 import (
    verify_password,
    get_password_hash,
    get_current_user
)
from app.models import User
from app.auth.jwt_handler import create_access_token
from datetime import timedelta


@pytest.mark.unit
@pytest.mark.auth
class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash format
    
    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_hash_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_hash_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "samepassword"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.asyncio
class TestGetCurrentUser:
    """Test get_current_user dependency."""
    
    async def test_get_current_user_valid_token(self, db_session, test_user):
        """Test getting user with valid token."""
        token = create_access_token(
            data={"sub": test_user.username, "email": test_user.email, "is_admin": test_user.is_admin},
            expires_delta=timedelta(minutes=30)
        )
        
        user = await get_current_user(token, db_session)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username
        assert user.email == test_user.email
    
    async def test_get_current_user_invalid_token(self, db_session):
        """Test getting user with invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await get_current_user(invalid_token, db_session)
    
    async def test_get_current_user_nonexistent_user(self, db_session):
        """Test getting user that doesn't exist."""
        token = create_access_token(
            data={"sub": "nonexistent", "email": "nonexistent@example.com", "is_admin": False},
            expires_delta=timedelta(minutes=30)
        )
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await get_current_user(token, db_session)
    
    async def test_get_current_user_expired_token(self, db_session, test_user):
        """Test getting user with expired token."""
        token = create_access_token(
            data={"sub": test_user.username, "email": test_user.email, "is_admin": test_user.is_admin},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await get_current_user(token, db_session)
