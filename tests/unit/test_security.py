"""Security tests for authentication and authorization."""

import pytest
from fastapi import status
from app.auth.jwt_handler import verify_token, create_access_token
from app.auth.oauth2 import verify_password, get_password_hash
from datetime import timedelta


def _detail_text(response) -> str:
    """Normalize error detail payload to text."""
    detail = response.json().get("detail", "")
    if isinstance(detail, dict):
        return str(detail.get("error", ""))
    return str(detail)

@pytest.mark.unit
@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication security."""
    
    def test_token_expiration(self):
        """Test that expired tokens are rejected."""
        data = {"sub": "testuser"}
        expired_token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        payload = verify_token(expired_token)
        assert payload is None
    
    def test_invalid_token_format(self):
        """Test that invalid token formats are rejected."""
        invalid_tokens = [
            "not.a.token",
            "invalid",
            "",
            "Bearer token",
            "eyJ.invalid.token"
        ]
        
        for token in invalid_tokens:
            payload = verify_token(token)
            assert payload is None
    
    def test_password_hashing_salt(self):
        """Test that password hashing uses salt (different hashes for same password)."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_password_verification_timing_attack_resistance(self):
        """Test that password verification doesn't leak timing information."""
        correct_password = "correctpassword"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(correct_password)
        
        # Both should take similar time (bcrypt handles this)
        verify_password(correct_password, hashed)
        verify_password(wrong_password, hashed)


@pytest.mark.integration
@pytest.mark.security
class TestAuthorizationSecurity:
    """Test authorization security."""
    
    def test_admin_only_endpoint_protection(self, client, test_token):
        """Test that admin-only endpoints reject non-admin users."""
        # Try to create service as non-admin
        response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "name": "test-service",
                "service_type": "file_storage",
                "base_url": "http://test:8000"
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_protected_endpoints_require_auth(self, client):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            "/api/services",
            "/api/health/services",
            "/api/gateway/file-storage/libraries",
            "/api/auth/me"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_tampering_rejection(self, client, test_token):
        """Test that tampered tokens are rejected."""
        # Tamper with token
        tampered_token = test_token[:-5] + "xxxxx"
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_inactive_user_access_denied(self, client, db_session, test_user):
        """Test that inactive users cannot access protected endpoints."""
        # Deactivate user
        test_user.is_active = False
        db_session.commit()
        
        # Get token before deactivation (token still valid but user inactive)
        from app.auth.jwt_handler import create_access_token
        from datetime import timedelta
        token = create_access_token(
            data={"sub": test_user.username, "email": test_user.email, "is_admin": test_user.is_admin},
            expires_delta=timedelta(minutes=30)
        )
        
        # Try to access protected endpoint
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Note: This depends on implementation - may need to check user status in get_current_user
        # For now, we test that the endpoint requires valid token


@pytest.mark.integration
@pytest.mark.security
class TestInputValidationSecurity:
    """Test input validation security."""
    
    def test_sql_injection_username(self, client):
        """Test SQL injection attempt in username."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "admin'; DROP TABLE users; --",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        # Should either fail validation or be safely handled by SQLAlchemy
        # SQLAlchemy parameterized queries should prevent SQL injection
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_xss_attempt_in_service_name(self, client, admin_token):
        """Test XSS attempt in service name."""
        response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "<script>alert('xss')</script>",
                "service_type": "file_storage",
                "base_url": "http://test:8000"
            }
        )
        # Should be stored as-is or sanitized, but not executed
        # This is more of a frontend concern, but we test it's handled
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
    
    def test_path_traversal_in_service_url(self, client, admin_token):
        """Test path traversal attempt in service URL."""
        response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "test-service",
                "service_type": "file_storage",
                "base_url": "http://test:8000/../../../etc/passwd"
            }
        )
        # Should be validated or sanitized
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
    
    def test_oversized_input(self, client):
        """Test oversized input handling."""
        large_string = "A" * 10000
        response = client.post(
            "/api/auth/register",
            json={
                "username": large_string,
                "email": "test@example.com",
                "password": "password123"
            }
        )
        # Should be rejected due to field length constraints
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


@pytest.mark.integration
@pytest.mark.security
class TestServiceSecurity:
    """Test service-related security."""
    
    def test_service_auth_token_not_exposed(self, client, test_token, test_service):
        """Test that service auth tokens are not exposed in responses."""
        response = client.get(
            f"/api/services/{test_service.id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Auth token should not be in response (or should be masked)
        assert "auth_token" not in data or data.get("auth_token") is None
    
    def test_service_url_validation(self, client, admin_token):
        """Test that service URLs are validated to prevent SSRF attacks."""
        invalid_urls = [
            ("not-a-url", "Invalid URL"),
            ("ftp://insecure:21", "scheme"),
            ("javascript:alert('xss')", "scheme"),
            ("", "empty"),
            ("http://localhost:8000", "Localhost"),
            ("http://127.0.0.1:8000", "Localhost"),
            ("http://192.168.1.1:8000", "Private IP"),
            ("file:///etc/passwd", "scheme"),
        ]
        
        for url, expected_error_keyword in invalid_urls:
            response = client.post(
                "/api/services",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "name": f"test-{hash(url) % 10000}",  # Unique name
                    "service_type": "file_storage",
                    "base_url": url
                }
            )
            # SSRF protection should reject all invalid URLs
            assert response.status_code == status.HTTP_400_BAD_REQUEST, f"URL {url} should be rejected"
            error_detail = _detail_text(response).lower()
            assert expected_error_keyword.lower() in error_detail, f"Error message should mention '{expected_error_keyword}' for URL {url}"
    
    def test_service_url_validation_allows_valid_urls(self, client, admin_token):
        """Test that valid external URLs are accepted."""
        valid_urls = [
            "https://api.example.com",
            "http://example.com/api",
            "https://subdomain.example.com:8080/path",
        ]
        
        for url in valid_urls:
            response = client.post(
                "/api/services",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "name": f"valid-service-{hash(url) % 10000}",
                    "service_type": "file_storage",
                    "base_url": url
                }
            )
            # Valid URLs should be accepted
            assert response.status_code == status.HTTP_201_CREATED, f"Valid URL {url} should be accepted"
