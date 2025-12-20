---
name: Remove hardcoded secrets
overview: Remove hardcoded default secrets from app/config.py and docker-compose.yml, making SECRET_KEY and JWT_SECRET_KEY required environment variables with validation. Update documentation to emphasize these must be set.
todos:
  - id: "1"
    content: "Update app/config.py: Remove default values for secret_key and jwt_secret_key, add Field() with min_length=32, and add field validators"
    status: completed
  - id: "2"
    content: "Update docker-compose.yml: Remove fallback defaults for SECRET_KEY and JWT_SECRET_KEY (lines 47-48, 337), make them required"
    status: completed
  - id: "3"
    content: "Update README.md: Emphasize SECRET_KEY and JWT_SECRET_KEY are REQUIRED in configuration section"
    status: completed
  - id: "4"
    content: "Update QUICKSTART.md: Add warnings that secrets are REQUIRED and app will fail without them"
    status: completed
  - id: "5"
    content: "Update docs/DEPLOYMENT.md: Mark secrets as REQUIRED in pre-deployment checklist and secret generation sections"
    status: completed
---

# Remove Hardcoded Default Secrets

## Overview

Remove security risks from hardcoded default secrets by making `SECRET_KEY` and `JWT_SECRET_KEY` required environment variables with validation. The application will fail to start with clear errors if these are not provided.

## Files to Modify

### 1. `app/config.py`

**Current Issues:**

- Line 14: `secret_key: str = "change-me-in-production"` (hardcoded default)
- Line 20: `jwt_secret_key: str = "change-me-in-production-jwt-secret"` (hardcoded default)

**Changes:**

- Remove default values for both fields
- Add Pydantic field validators to enforce minimum length (32 characters)
- Use `Field()` with validation to make them required and validate length
- Add clear error messages if validation fails

**Implementation:**

```python
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str = Field(..., min_length=32, description="Application secret key (REQUIRED)")
    jwt_secret_key: str = Field(..., min_length=32, description="JWT secret key (REQUIRED)")
    
    @field_validator('secret_key', 'jwt_secret_key')
    @classmethod
    def validate_secret_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(f"Secret must be at least 32 characters long, got {len(v)}")
        return v
```



### 2. `docker-compose.yml`

**Current Issues:**

- Line 47: `SECRET_KEY: ${SECRET_KEY:-change-me-in-production}` (fallback default)
- Line 48: `JWT_SECRET_KEY: ${JWT_SECRET_KEY:-change-me-in-production-jwt}` (fallback default)
- Line 337: `JWT_SECRET_KEY: ${JWT_SECRET_KEY:-change-me-in-production-jwt}` (education-service)

**Changes:**

- Remove fallback defaults (`:-value` syntax)
- Make environment variables required: `SECRET_KEY: ${SECRET_KEY}` and `JWT_SECRET_KEY: ${JWT_SECRET_KEY}`
- Update education-service environment (line 337) to match
- Add comments indicating these are required

**Note:** Other default passwords in docker-compose.yml (postgres, seafile, gitea, etc.) are service-specific and not part of this task, but could be addressed separately.

### 3. Documentation Updates

#### `README.md`

- Update "Configuration" section (around line 111-114)
- Emphasize that `SECRET_KEY` and `JWT_SECRET_KEY` are **REQUIRED** and must be set
- Add warning about application failing to start if not set

#### `QUICKSTART.md`

- Update Step 1 (lines 17-21) to emphasize secrets are **REQUIRED**
- Add note that application will not start without these variables
- Update troubleshooting section if needed

#### `docs/DEPLOYMENT.md`

- Update "Application Secrets" section (lines 30-32) to mark as **REQUIRED**
- Emphasize in pre-deployment checklist that these must be set
- Update secret generation section to emphasize these are mandatory

## Validation Strategy

### Pydantic Validation

- Use `Field(..., min_length=32)` to enforce minimum length
- Add custom validator for clearer error messages
- Validation happens at Settings instantiation, so app fails fast on startup

### Error Messages

- Clear validation errors: "Secret must be at least 32 characters long"
- Missing field errors from Pydantic will indicate which variable is missing
- Application startup will fail immediately with descriptive error

## Testing Considerations

After implementation:

1. Test that app fails to start without `SECRET_KEY` set
2. Test that app fails to start without `JWT_SECRET_KEY` set
3. Test that app fails with secrets shorter than 32 characters
4. Test that app starts successfully with valid secrets (32+ chars)
5. Verify docker-compose fails gracefully when variables are missing