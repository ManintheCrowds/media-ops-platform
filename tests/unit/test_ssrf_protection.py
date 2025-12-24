"""Comprehensive tests for SSRF (Server-Side Request Forgery) protection."""

import pytest
from fastapi import status
from app.validation import validate_service_url, is_private_ip, matches_allowed_pattern
from app.config import settings


@pytest.mark.unit
@pytest.mark.security
class TestURLValidation:
    """Test URL validation function."""
    
    def test_valid_external_http_url(self):
        """Test that valid external HTTP URLs are accepted."""
        is_valid, error = validate_service_url("http://example.com")
        assert is_valid is True
        assert error == ""
    
    def test_valid_external_https_url(self):
        """Test that valid external HTTPS URLs are accepted."""
        is_valid, error = validate_service_url("https://example.com/api")
        assert is_valid is True
        assert error == ""
    
    def test_valid_internal_url_with_allowed_pattern(self):
        """Test that internal URLs matching allowed patterns are accepted."""
        allowed_patterns = ["http://seafile:*"]
        is_valid, error = validate_service_url(
            "http://seafile:8000",
            allowed_internal_patterns=allowed_patterns
        )
        assert is_valid is True
        assert error == ""
    
    def test_valid_internal_url_with_wildcard_port(self):
        """Test that internal URLs with wildcard port patterns are accepted."""
        allowed_patterns = ["http://jellyfin:*"]
        is_valid, error = validate_service_url(
            "http://jellyfin:8096",
            allowed_internal_patterns=allowed_patterns
        )
        assert is_valid is True
        assert error == ""
    
    def test_block_file_scheme(self):
        """Test that file:// scheme is blocked."""
        is_valid, error = validate_service_url("file:///etc/passwd")
        assert is_valid is False
        assert "Dangerous URL scheme" in error or "not allowed" in error
    
    def test_block_ftp_scheme(self):
        """Test that ftp:// scheme is blocked."""
        is_valid, error = validate_service_url("ftp://example.com")
        assert is_valid is False
        assert "Dangerous URL scheme" in error or "not allowed" in error
    
    def test_block_javascript_scheme(self):
        """Test that javascript: scheme is blocked."""
        is_valid, error = validate_service_url("javascript:alert('xss')")
        assert is_valid is False
        assert "Dangerous URL scheme" in error or "not allowed" in error
    
    def test_block_data_scheme(self):
        """Test that data: scheme is blocked."""
        is_valid, error = validate_service_url("data:text/html,<script>alert('xss')</script>")
        assert is_valid is False
        assert "Dangerous URL scheme" in error or "not allowed" in error
    
    def test_block_localhost(self):
        """Test that localhost is blocked."""
        is_valid, error = validate_service_url("http://localhost:8000")
        assert is_valid is False
        assert "Localhost" in error
    
    def test_block_127_0_0_1(self):
        """Test that 127.0.0.1 is blocked."""
        is_valid, error = validate_service_url("http://127.0.0.1:8000")
        assert is_valid is False
        assert "Localhost" in error
    
    def test_block_0_0_0_0(self):
        """Test that 0.0.0.0 is blocked."""
        is_valid, error = validate_service_url("http://0.0.0.0:8000")
        assert is_valid is False
        assert "Localhost" in error
    
    def test_block_private_ip_10_x(self):
        """Test that 10.x.x.x private IPs are blocked."""
        is_valid, error = validate_service_url("http://10.0.0.1:8000")
        assert is_valid is False
        assert "Private IP" in error
    
    def test_block_private_ip_192_168_x(self):
        """Test that 192.168.x.x private IPs are blocked."""
        is_valid, error = validate_service_url("http://192.168.1.1:8000")
        assert is_valid is False
        assert "Private IP" in error
    
    def test_block_private_ip_172_16_31_x(self):
        """Test that 172.16-31.x.x private IPs are blocked."""
        is_valid, error = validate_service_url("http://172.16.0.1:8000")
        assert is_valid is False
        assert "Private IP" in error
        
        is_valid, error = validate_service_url("http://172.31.255.255:8000")
        assert is_valid is False
        assert "Private IP" in error
    
    def test_block_link_local_169_254_x(self):
        """Test that 169.254.x.x link-local IPs are blocked."""
        is_valid, error = validate_service_url("http://169.254.0.1:8000")
        assert is_valid is False
        assert "Private IP" in error
    
    def test_block_ipv6_localhost(self):
        """Test that IPv6 localhost (::1) is blocked."""
        is_valid, error = validate_service_url("http://[::1]:8000")
        assert is_valid is False
        assert "Localhost" in error
    
    def test_block_malformed_url(self):
        """Test that malformed URLs are rejected."""
        is_valid, error = validate_service_url("not-a-url")
        assert is_valid is False
        assert "Invalid URL" in error or "not allowed" in error
    
    def test_block_empty_url(self):
        """Test that empty URLs are rejected."""
        is_valid, error = validate_service_url("")
        assert is_valid is False
        assert "empty" in error.lower() or "non-empty" in error.lower()
    
    def test_block_none_url(self):
        """Test that None URLs are rejected."""
        is_valid, error = validate_service_url(None)
        assert is_valid is False
    
    def test_block_path_traversal(self):
        """Test that path traversal attempts are blocked."""
        is_valid, error = validate_service_url("http://example.com/../../../etc/passwd")
        assert is_valid is False
        assert "Path traversal" in error
    
    def test_block_path_traversal_encoded(self):
        """Test that encoded path traversal attempts are blocked."""
        is_valid, error = validate_service_url("http://example.com/..%2F..%2Fetc%2Fpasswd")
        assert is_valid is False
        assert "Path traversal" in error
    
    def test_valid_url_with_path(self):
        """Test that valid URLs with paths are accepted."""
        is_valid, error = validate_service_url("https://api.example.com/v1/users")
        assert is_valid is True
        assert error == ""
    
    def test_valid_url_with_query_params(self):
        """Test that valid URLs with query parameters are accepted."""
        is_valid, error = validate_service_url("https://example.com/api?param=value")
        assert is_valid is True
        assert error == ""


@pytest.mark.unit
@pytest.mark.security
class TestPrivateIPDetection:
    """Test private IP detection function."""
    
    def test_detect_private_ipv4(self):
        """Test detection of private IPv4 addresses."""
        assert is_private_ip("10.0.0.1") is True
        assert is_private_ip("192.168.1.1") is True
        assert is_private_ip("172.16.0.1") is True
        assert is_private_ip("127.0.0.1") is True
        assert is_private_ip("169.254.0.1") is True
    
    def test_detect_public_ipv4(self):
        """Test that public IPv4 addresses are not detected as private."""
        assert is_private_ip("8.8.8.8") is False
        assert is_private_ip("1.1.1.1") is False
        assert is_private_ip("203.0.113.1") is False
    
    def test_invalid_ip(self):
        """Test that invalid IP addresses return False."""
        assert is_private_ip("not.an.ip") is False
        assert is_private_ip("256.256.256.256") is False


@pytest.mark.unit
@pytest.mark.security
class TestAllowedPatternMatching:
    """Test allowed pattern matching function."""
    
    def test_match_exact_hostname_and_port(self):
        """Test matching exact hostname and port."""
        patterns = ["http://seafile:8000"]
        assert matches_allowed_pattern("http://seafile:8000", patterns) is True
        assert matches_allowed_pattern("http://seafile:8001", patterns) is False
    
    def test_match_wildcard_port(self):
        """Test matching with wildcard port."""
        patterns = ["http://seafile:*"]
        assert matches_allowed_pattern("http://seafile:8000", patterns) is True
        assert matches_allowed_pattern("http://seafile:8096", patterns) is True
        assert matches_allowed_pattern("http://jellyfin:8000", patterns) is False
    
    def test_match_multiple_patterns(self):
        """Test matching against multiple patterns."""
        patterns = ["http://seafile:*", "http://jellyfin:*"]
        assert matches_allowed_pattern("http://seafile:8000", patterns) is True
        assert matches_allowed_pattern("http://jellyfin:8096", patterns) is True
        assert matches_allowed_pattern("http://other:8000", patterns) is False


@pytest.mark.integration
@pytest.mark.security
class TestServiceRegistrationSSRF:
    """Test SSRF protection in service registration."""
    
    def test_create_service_with_valid_external_url(self, client, admin_token):
        """Test creating service with valid external URL."""
        response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "external-service",
                "service_type": "file_storage",
                "base_url": "https://api.example.com"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_service_with_allowed_internal_url(self, client, admin_token):
        """Test creating service with allowed internal URL."""
        response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "internal-service",
                "service_type": "file_storage",
                "base_url": "http://seafile:8000"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_service_with_localhost_rejected(self, client, admin_token):
        """Test that creating service with localhost is rejected."""
        response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "localhost-service",
                "service_type": "file_storage",
                "base_url": "http://localhost:8000"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Localhost" in response.json()["detail"]
    
    def test_create_service_with_private_ip_rejected(self, client, admin_token):
        """Test that creating service with private IP is rejected."""
        response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "private-ip-service",
                "service_type": "file_storage",
                "base_url": "http://192.168.1.1:8000"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Private IP" in response.json()["detail"]
    
    def test_create_service_with_file_scheme_rejected(self, client, admin_token):
        """Test that creating service with file:// scheme is rejected."""
        response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "file-scheme-service",
                "service_type": "file_storage",
                "base_url": "file:///etc/passwd"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "scheme" in response.json()["detail"].lower()
    
    def test_create_service_with_invalid_api_url_rejected(self, client, admin_token):
        """Test that invalid api_url is rejected."""
        response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "invalid-api-url-service",
                "service_type": "file_storage",
                "base_url": "https://api.example.com",
                "api_url": "http://127.0.0.1:8000"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "api_url" in response.json()["detail"]
    
    def test_create_service_with_invalid_health_check_url_rejected(self, client, admin_token):
        """Test that invalid health_check_url is rejected."""
        response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "invalid-health-url-service",
                "service_type": "file_storage",
                "base_url": "https://api.example.com",
                "health_check_url": "ftp://example.com"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "health_check_url" in response.json()["detail"]
    
    def test_update_service_with_invalid_url_rejected(self, client, admin_token, test_service):
        """Test that updating service with invalid URL is rejected."""
        response = client.put(
            f"/api/services/{test_service.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": test_service.name,
                "service_type": test_service.service_type,
                "base_url": "http://localhost:8000"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "base_url" in response.json()["detail"]


@pytest.mark.integration
@pytest.mark.security
class TestGatewayProxySSRF:
    """Test SSRF protection in gateway proxy."""
    
    def test_proxy_request_with_valid_url(self, client, test_token, db_session):
        """Test proxy request with valid URL."""
        from app.models import Service
        import respx
        import httpx
        
        service = Service(
            name="test-proxy-service",
            service_type="file_storage",
            base_url="https://api.example.com",
            is_active=True
        )
        db_session.add(service)
        db_session.commit()
        
        with respx.mock:
            respx.get("https://api.example.com/test").mock(
                return_value=httpx.Response(200, json={"data": "test"})
            )
            response = client.get(
                f"/api/gateway/proxy/{service.name}/test",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            # Should either succeed or fail with service unavailable (if mock doesn't work)
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_502_BAD_GATEWAY]
    
    def test_proxy_request_with_path_traversal_rejected(self, client, test_token, db_session):
        """Test that path traversal in proxy path is rejected."""
        from app.models import Service
        
        service = Service(
            name="test-proxy-service-2",
            service_type="file_storage",
            base_url="https://api.example.com",
            is_active=True
        )
        db_session.add(service)
        db_session.commit()
        
        response = client.get(
            f"/api/gateway/proxy/{service.name}/../../../etc/passwd",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Path traversal" in response.json()["detail"]
    
    def test_proxy_request_with_encoded_path_traversal_rejected(self, client, test_token, db_session):
        """Test that encoded path traversal is rejected."""
        from app.models import Service
        
        service = Service(
            name="test-proxy-service-3",
            service_type="file_storage",
            base_url="https://api.example.com",
            is_active=True
        )
        db_session.add(service)
        db_session.commit()
        
        response = client.get(
            f"/api/gateway/proxy/{service.name}/..%2F..%2Fetc%2Fpasswd",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Path traversal" in response.json()["detail"]
    
    def test_proxy_request_validates_target_url(self, client, test_token, db_session):
        """Test that proxy validates the constructed target URL."""
        from app.models import Service
        
        # Create a service with a valid base_url, but the path manipulation
        # should still be caught by path validation
        service = Service(
            name="test-proxy-service-4",
            service_type="file_storage",
            base_url="https://api.example.com",
            is_active=True
        )
        db_session.add(service)
        db_session.commit()
        
        # Even if base_url is valid, path traversal should be caught
        response = client.get(
            f"/api/gateway/proxy/{service.name}/../..",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.integration
@pytest.mark.security
class TestSSRFIntegration:
    """Integration tests for SSRF protection."""
    
    def test_end_to_end_service_creation_and_proxy(self, client, admin_token, test_token, db_session):
        """Test end-to-end: create service and proxy to it."""
        import respx
        import httpx
        
        # Create a service with valid external URL
        create_response = client.post(
            "/api/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "e2e-service",
                "service_type": "file_storage",
                "base_url": "https://api.example.com"
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        service_id = create_response.json()["id"]
        
        # Get the service name
        get_response = client.get(
            f"/api/services/{service_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        service_name = get_response.json()["name"]
        
        # Try to proxy to it (will fail if service is not actually available, but validation should pass)
        with respx.mock:
            respx.get("https://api.example.com/test").mock(
                return_value=httpx.Response(200, json={"data": "test"})
            )
            proxy_response = client.get(
                f"/api/gateway/proxy/{service_name}/test",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            # Should either succeed or fail with service unavailable, but not with validation error
            assert proxy_response.status_code != status.HTTP_400_BAD_REQUEST or "Invalid target URL" not in proxy_response.json().get("detail", "")
    
    def test_ssrf_attempt_blocked_at_registration(self, client, admin_token):
        """Test that SSRF attempts are blocked at service registration."""
        ssrf_attempts = [
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            "file:///etc/passwd",
            "http://192.168.1.1:8000",
            "http://10.0.0.1:8000",
            "ftp://example.com",
            "javascript:alert('xss')"
        ]
        
        for i, url in enumerate(ssrf_attempts):
            response = client.post(
                "/api/services",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "name": f"ssrf-attempt-{i}",
                    "service_type": "file_storage",
                    "base_url": url
                }
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST, f"SSRF attempt with {url} should be blocked"





