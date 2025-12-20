"""Unit tests for JWT handler."""

import pytest
from datetime import timedelta, datetime, timezone
from jose import jwt
from app.auth.jwt_handler import create_access_token, verify_token
from app.config import settings


@pytest.mark.unit
@pytest.mark.auth
class TestJWTHandler:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "testuser", "email": "test@example.com", "is_admin": False}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        assert payload["sub"] == "testuser"
        assert payload["email"] == "test@example.com"
        assert payload["is_admin"] is False
        assert "exp" in payload
    
    def test_create_access_token_with_expiration(self):
        """Test creating token with custom expiration."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta=expires_delta)
        
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check expiration is approximately 60 minutes from now
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.now(timezone.utc)
        diff = exp_time - now
        
        assert 59 <= diff.total_seconds() / 60 <= 61
    
    def test_verify_token_valid(self):
        """Test verifying a valid token."""
        data = {"sub": "testuser", "email": "test@example.com"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["email"] == "test@example.com"
    
    def test_verify_token_invalid(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = verify_token(invalid_token)
        
        assert payload is None
    
    def test_verify_token_expired(self):
        """Test verifying an expired token."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta=expires_delta)
        
        payload = verify_token(token)
        
        # Should return None for expired token
        assert payload is None
    
    def test_verify_token_wrong_secret(self):
        """Test verifying token with wrong secret."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Try to decode with wrong secret
        try:
            jwt.decode(
                token,
                "wrong-secret-key",
                algorithms=[settings.jwt_algorithm]
            )
            assert False, "Should have raised an exception"
        except jwt.JWTError:
            pass  # Expected
    
    def test_token_contains_required_fields(self):
        """Test that token contains all required fields."""
        data = {"sub": "testuser", "email": "test@example.com", "is_admin": True}
        token = create_access_token(data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert "sub" in payload
        assert "email" in payload
        assert "is_admin" in payload
        assert "exp" in payload
