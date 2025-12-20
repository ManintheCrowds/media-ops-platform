---
name: Gateway Request Limits
overview: Add configurable request size limits and per-service timeout configuration to the gateway proxy endpoints, with improved error handling for oversized requests and timeouts to prevent DoS vulnerabilities.
todos:
  - id: config-settings
    content: Add max_request_size_mb and service_timeouts configuration to app/config.py Settings class
    status: completed
  - id: size-validation
    content: Add request size validation in proxy_to_service() - check Content-Length header and validate body size after reading
    status: completed
  - id: timeout-config
    content: Update proxy_request() to use per-service timeout configuration from settings
    status: completed
  - id: error-handling
    content: Enhance error handling for httpx.TimeoutException and oversized requests with appropriate HTTP status codes and messages
    status: completed
---

# Gateway Request Size Limits and Error Handling

## Overview

Add request size limits and configurable timeouts to the gateway proxy endpoints in `app/api/gateway.py` to prevent resource exhaustion attacks. Configuration will be added to `app/config.py`.

## Implementation Details

### 1. Configuration Updates (`app/config.py`)

Add new settings to the `Settings` class:

- `max_request_size_mb: float = 10.0` - Maximum request body size in megabytes (default 10MB)
- `service_timeouts: dict[str, float]` - Per-service-type timeout configuration in seconds
- Default mapping: `{"file_storage": 60.0, "media_server": 120.0, "productivity": 30.0, "dev_tools": 45.0, "monitoring": 30.0, "security": 30.0}`
- Default timeout for unknown service types: 30.0 seconds

### 2. Gateway Proxy Updates (`app/api/gateway.py`)

#### Size Validation in `proxy_to_service()`

- Check `Content-Length` header before reading body (if present)
- Convert max size to bytes: `max_size_bytes = settings.max_request_size_mb * 1024 * 1024`
- If `Content-Length` exceeds limit, raise `HTTPException(413, detail="Request body too large")` immediately
- After reading body with `await request.body()`, validate actual size
- If body exceeds limit, raise `HTTPException(413, detail="Request body exceeds maximum allowed size")`

#### Timeout Configuration in `proxy_request()`

- Import `settings` from `app.config`
- Get timeout for service type: `timeout = settings.service_timeouts.get(service.service_type, 30.0)`
- Pass timeout to `httpx.AsyncClient(timeout=timeout)`

#### Enhanced Error Handling

- Catch `httpx.TimeoutException` specifically:
- Raise `HTTPException(504, detail=f"Service request timed out after {timeout} seconds")`
- Catch `httpx.RequestError` (existing, keep for other network errors):
- Improve error message: `detail=f"Service unavailable: {str(e)}"`
- Add validation error for oversized requests:
- `HTTPException(413, detail=f"Request body exceeds maximum allowed size of {settings.max_request_size_mb}MB")`

### 3. Error Response Format

All error responses should include:

- Appropriate HTTP status codes:
- `413 Payload Too Large` for size limit violations
- `504 Gateway Timeout` for timeout errors
- `502 Bad Gateway` for other service errors
- Clear, user-friendly error messages with relevant details (size limit, timeout duration)

## Files to Modify

1. **`app/config.py`**

- Add `max_request_size_mb` field
- Add `service_timeouts` field with default dictionary

2. **`app/api/gateway.py`**

- Import `settings` from `app.config`
- Add size validation logic in `proxy_to_service()`
- Update `proxy_request()` to use per-service timeouts
- Enhance error handling for timeouts and size limits

## Security Benefits

- Prevents DoS attacks via large request bodies
- Configurable timeouts prevent resource exhaustion from slow services