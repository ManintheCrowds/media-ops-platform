---
name: Strengthen Debug Security
overview: Add multiple security layers to debug endpoints, sanitize error messages in production, add logging for debug access, and provide migration path away from /init-db endpoint.
todos:
  - id: config-security-settings
    content: Add enable_debug_endpoints, debug_endpoint_allowed_ips, and debug_endpoint_require_admin settings to app/config.py
    status: completed
  - id: secure-init-db-endpoint
    content: Replace simple debug check in /init-db endpoint with multiple security layers (explicit flag, admin auth, IP whitelist) and add logging
    status: completed
  - id: global-exception-handler
    content: Add global exception handler in app/main.py to sanitize error messages in production while logging full details server-side
    status: completed
  - id: sanitize-health-errors
    content: Update app/api/health.py to sanitize error messages in production (lines 59, 79, 124)
    status: completed
  - id: setup-logging
    content: Configure logging in app/main.py for security events and debug endpoint access
    status: completed
  - id: update-fastapi-debug
    content: Make FastAPI debug mode more restrictive by requiring both debug and enable_debug_endpoints flags
    status: completed
  - id: document-migration
    content: Add Alembic migration documentation to docs/DEVELOPMENT.md with deprecation notice for /init-db
    status: completed
  - id: update-security-docs
    content: Add debug mode security section to docs/SECURITY.md explaining risks and best practices
    status: completed
---

# Strengthen Debug Mode Checks and Prevent Information Leakage

## Current Security Issues

1. **`/init-db` endpoint** (`app/auth/oauth2.py:164-174`) only checks `settings.debug` flag
2. **FastAPI debug mode** (`app/main.py:17`) can expose detailed error traces in production
3. **Error messages** in `app/api/health.py` expose exception details (lines 59, 79, 124)
4. **No logging** for debug endpoint access attempts
5. **No IP whitelist** or additional authentication for debug endpoints
6. **No global exception handler** to sanitize error messages based on debug mode

## Implementation Plan

### 1. Enhance Configuration (`app/config.py`)

Add new security settings:

- `enable_debug_endpoints: bool = False` - Explicit flag for debug endpoints (separate from FastAPI debug)
- `debug_endpoint_allowed_ips: list[str] = []` - IP whitelist for debug endpoints
- `debug_endpoint_require_admin: bool = True` - Require admin authentication even in debug mode

These settings provide defense-in-depth beyond just the `debug` flag.

### 2. Secure `/init-db` Endpoint (`app/auth/oauth2.py`)

Replace the simple debug check with multiple security layers:

```python
@router.post("/init-db")
async def init_database(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Initialize database tables (development only - requires explicit enable)."""
    # Layer 1: Check explicit enable flag
    if not settings.enable_debug_endpoints:
        logger.warning(f"Blocked /init-db access from {request.client.host}")
        raise HTTPException(status_code=404, detail="Not found")
    
    # Layer 2: Require admin authentication
    if settings.debug_endpoint_require_admin and not current_user.is_admin:
        logger.warning(f"Blocked /init-db access - non-admin user: {current_user.username}")
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Layer 3: IP whitelist check
    if settings.debug_endpoint_allowed_ips:
        client_ip = request.client.host
        if client_ip not in settings.debug_endpoint_allowed_ips:
            logger.warning(f"Blocked /init-db access from unauthorized IP: {client_ip}")
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Log successful access
    logger.info(f"Database initialization triggered by admin user: {current_user.username} from {request.client.host}")
    
    Base.metadata.create_all(bind=engine)
    return {"message": "Database initialized"}
```



### 3. Add Global Exception Handler (`app/main.py`)

Add a global exception handler that sanitizes error messages in production:

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that sanitizes error messages in production."""
    # Log full error details server-side
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Return sanitized error to client
    if settings.debug:
        # In debug mode, return detailed error
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
                "path": str(request.url)
            }
        )
    else:
        # In production, return generic error
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred"}
        )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with appropriate detail level."""
    if settings.debug:
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "body": exc.body}
        )
    else:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid request data"}
        )
```



### 4. Sanitize Error Messages in Health Endpoints (`app/api/health.py`)

Update error handling to not expose exception details in production:

- Line 59: Remove `"error": str(e)` from production responses
- Line 79: Sanitize error message in exception handler
- Line 124: Remove `"error": str(e)` from production responses

Use pattern:

```python
except Exception as e:
    logger.error(f"Error checking service {service.name}: {e}", exc_info=True)
    error_detail = str(e) if settings.debug else "Service check failed"
    # ... return sanitized error
```



### 5. Add Logging Configuration (`app/main.py`)

Set up logging for security events:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

security_logger = logging.getLogger("security")
```



### 6. Update FastAPI Debug Setting (`app/main.py`)

Ensure FastAPI debug mode is only enabled when explicitly configured:

```python
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug and settings.enable_debug_endpoints  # More restrictive
)
```



### 7. Document Migration Path (`docs/DEVELOPMENT.md`)

Add section recommending:

- Use Alembic migrations instead of `/init-db` endpoint
- Steps to set up Alembic (similar to education-service)
- Deprecation notice for `/init-db` endpoint

### 8. Update Security Documentation (`docs/SECURITY.md`)

Add section on debug mode security:

- Explain security implications of debug mode
- Document new configuration options
- Provide best practices for development vs production
- Warn about information leakage risks

## Files to Modify

1. `app/config.py` - Add new security configuration options
2. `app/auth/oauth2.py` - Secure `/init-db` endpoint with multiple layers
3. `app/main.py` - Add global exception handlers and logging
4. `app/api/health.py` - Sanitize error messages
5. `docs/DEVELOPMENT.md` - Document migration to Alembic
6. `docs/SECURITY.md` - Document debug mode security implications

## Security Improvements

- **Defense in depth**: Multiple security layers (explicit flag, admin auth, IP whitelist)
- **Information hiding**: Error messages sanitized in production
- **Audit trail**: All debug endpoint access logged
- **Fail secure**: Default deny, require explicit enable
- **Separation of concerns**: FastAPI debug separate from debug endpoints

## Migration Considerations

The `/init-db` endpoint should eventually be removed in favor of Alembic migrations. This plan: