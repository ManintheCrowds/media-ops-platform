---
name: SSRF Protection Implementation
overview: Add comprehensive URL validation to prevent SSRF attacks by validating service URLs at registration and during proxy requests, blocking dangerous schemes and private IP ranges while allowing configured internal services.
todos:
  - id: create-validation-module
    content: Create app/validation.py with validate_service_url() function that blocks dangerous schemes, localhost, and private IP ranges while allowing configured internal patterns
    status: completed
  - id: update-config
    content: Add ssrf_allowed_internal_patterns configuration to app/config.py for legitimate Docker internal services
    status: completed
  - id: integrate-service-validation
    content: Add URL validation to create_service() and update_service() endpoints in app/api/services.py for base_url, api_url, and health_check_url
    status: completed
  - id: integrate-gateway-validation
    content: Add URL validation to proxy_request() function and proxy_to_service() endpoint in app/api/gateway.py before making HTTP requests
    status: completed
  - id: create-ssrf-tests
    content: Create tests/unit/test_ssrf_protection.py with comprehensive tests for URL validation, service registration, and gateway proxy SSRF prevention
    status: completed
  - id: update-existing-security-tests
    content: Update test_service_url_validation() in tests/unit/test_security.py to verify SSRF protection is working
    status: completed
---

# SSRF Protection Implementation Plan

## Overview

Implement URL validation to prevent Server-Side Request Forgery (SSRF) attacks by validating all service URLs before they are registered or used for proxying requests.

## Architecture

The validation will be implemented in three layers:

1. **Validation Module** (`app/validation.py`) - Core validation logic
2. **Configuration** (`app/config.py`) - Allowlist for legitimate internal services
3. **Integration Points** - Service registration and gateway proxy

## Implementation Details

### 1. Create URL Validation Module (`app/validation.py`)

Create a new validation module with the following functions:

- `validate_service_url(url: str, allowed_internal_patterns: list[str] = None) -> tuple[bool, str]`
- Returns `(is_valid, error_message)`
- Validates URL scheme (only `http://` and `https://`)
- Blocks dangerous schemes: `file://`, `ftp://`, `gopher://`, `javascript:`, `data:`, etc.
- Validates URL format using `urllib.parse.urlparse`
- Checks for localhost variations: `localhost`, `127.0.0.1`, `0.0.0.0`, `::1`
- Blocks private IP ranges:
    - `10.0.0.0/8` (10.x.x.x)
    - `192.168.0.0/16` (192.168.x.x)
    - `172.16.0.0/12` (172.16-31.x.x)
    - `169.254.0.0/16` (link-local)
    - `127.0.0.0/8` (loopback)
- Allows configured internal service patterns (e.g., `http://seafile:*`, `http://jellyfin:*`)
- Handles IPv6 addresses and checks for IPv6 localhost/private ranges
- `is_private_ip(ip: str) -> bool`
- Helper function to check if an IP address is in private ranges
- Supports both IPv4 and IPv6
- `matches_allowed_pattern(url: str, patterns: list[str]) -> bool`
- Helper function to check if URL matches any allowed internal service pattern
- Supports wildcards for hostnames and ports

### 2. Update Configuration (`app/config.py`)

Add configuration for allowed internal service patterns:

```python
# SSRF Protection
ssrf_allowed_internal_patterns: list[str] = [
    "http://seafile:*",
    "http://jellyfin:*",
    "http://bookstack:*",
    "http://gitea:*",
    "http://prometheus:*",
    "http://grafana:*",
    "http://vaultwarden:*",
    "http://postgres:*",
    "http://platform:*"
]
```

These patterns allow legitimate Docker internal service communication while blocking external SSRF attempts.

### 3. Integrate Validation in Service Registration (`app/api/services.py`)

Update `create_service()` and `update_service()` endpoints:

- Import validation function
- Validate `base_url`, `api_url`, and `health_check_url` (if provided)
- Raise `HTTPException` with status 400 and descriptive error message if validation fails
- Apply validation before creating/updating the service in the database

### 4. Integrate Validation in Gateway Proxy (`app/api/gateway.py`)

Update `proxy_request()` function:

- Validate the constructed `target_url` before making the HTTP request
- Validate the `path` parameter to prevent path-based SSRF (e.g., `../../../etc/passwd`)
- Raise `HTTPException` with status 400 if validation fails
- Apply validation in `proxy_to_service()` endpoint as well

### 5. Add Comprehensive Tests (`tests/unit/test_ssrf_protection.py`)

Create a new test file with the following test cases:**URL Validation Tests:**

- Valid external URLs (https://example.com)
- Valid internal URLs matching allowed patterns
- Invalid schemes (file://, ftp://, javascript:, data:)
- Localhost variations (localhost, 127.0.0.1, 0.0.0.0, ::1)
- Private IP ranges (10.x, 192.168.x, 172.16-31.x)
- IPv6 private/localhost addresses
- Malformed URLs
- Empty/null URLs

**Service Registration Tests:**

- Valid service registration with external URL
- Valid service registration with allowed internal pattern
- Invalid service registration with localhost
- Invalid service registration with private IP
- Invalid service registration with dangerous scheme
- Update service with invalid URL

**Gateway Proxy Tests:**

- Valid proxy request
- Invalid proxy request to localhost
- Invalid proxy request to private IP
- Path traversal attempts in path parameter
- SSRF attempt via service.base_url manipulation

**Integration Tests:**

- End-to-end service creation and proxy flow
- Verify validation errors are properly returned
- Verify allowed internal services work correctly

## Files to Modify

1. **New File**: `app/validation.py` - URL validation functions
2. **Modify**: `app/config.py` - Add SSRF configuration
3. **Modify**: `app/api/services.py` - Add validation to create/update endpoints
4. **Modify**: `app/api/gateway.py` - Add validation to proxy functions
5. **New File**: `tests/unit/test_ssrf_protection.py` - Comprehensive SSRF tests
6. **Modify**: `tests/unit/test_security.py` - Update existing URL validation test

## Security Considerations

- **Defense in Depth**: Validation at both registration and proxy time
- **Whitelist Approach**: Only allow configured internal services, deny all others