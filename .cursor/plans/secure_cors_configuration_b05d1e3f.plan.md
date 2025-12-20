---
name: Secure CORS Configuration
overview: Restrict CORS defaults to prevent credential exposure by changing default origins to empty list, adding validation to prevent wildcard origins with credentials enabled, adding warning logs for permissive configurations, and updating security documentation with production examples.
todos:
  - id: "1"
    content: Change default cors_origins from ['*'] to [] in app/config.py
    status: completed
  - id: "2"
    content: Add Pydantic v2 model_validator to prevent wildcard origins with credentials enabled
    status: completed
  - id: "3"
    content: Add warning logging for insecure CORS configurations in non-debug mode
    status: completed
  - id: "4"
    content: Update docs/SECURITY.md CORS section with production examples and environment variable documentation
    status: completed
---

# Secure CORS Configuration Plan

## Overview

The current CORS configuration in `app/config.py` defaults to `cors_origins=["*"] `with `cors_allow_credentials=True`, creating a CSRF vulnerability. This plan implements secure defaults and validation to prevent accidental credential exposure.

## Changes Required

### 1. Update `app/config.py`

**Change default CORS origins:**

- Change `cors_origins: list[str] = ["*"]` to `cors_origins: list[str] = []` (line 44)

**Add Pydantic v2 validation:**

- Import `model_validator` from `pydantic`
- Add a `@model_validator` method to validate that if `cors_allow_credentials` is `True`, `cors_origins` cannot contain `"*"`
- Raise `ValueError` with a clear message if validation fails

**Add warning log for permissive CORS:**

- Import `logging` module
- Create a logger instance
- In the `@model_validator` method or after settings initialization, log a warning if:
- `cors_origins` contains `"*"` and `cors_allow_credentials` is `True` (this will be caught by validation, but log before raising)
- OR if `cors_origins` is empty and `cors_allow_credentials` is `True` in non-debug mode (insecure configuration)
- The warning should guide users to configure specific origins

**Implementation details:**

- Use Pydantic v2's `@model_validator(mode='after')` for cross-field validation
- The validator should check both conditions and provide helpful error messages
- Add logging import and setup at module level

### 2. Update `app/main.py`

**Add startup warning:**

- Optionally add a startup event handler that logs a warning if CORS configuration is insecure
- This provides runtime visibility in addition to validation

### 3. Update `docs/SECURITY.md`

**Enhance CORS Configuration section (lines 159-174):**

- Update the existing CORS section with:
- Clear explanation of the security risk with wildcard origins + credentials
- Production configuration examples with specific origins
- Development configuration examples
- Environment variable examples showing proper configuration
- Warning about the default secure configuration requiring explicit setup
- Best practices for CORS configuration

**Add environment variable examples:**

- Show how to set `CORS_ORIGINS` as a comma-separated list or JSON array
- Include examples for both development and production
- Explain the relationship between `CORS_ORIGINS` and `CORS_ALLOW_CREDENTIALS`

## Implementation Details

### Validation Logic

```python
@model_validator(mode='after')
def validate_cors_config(self):
    if self.cors_allow_credentials:
        if "*" in self.cors_origins:
            raise ValueError(
                "CORS configuration error: cors_allow_credentials cannot be True "
                "when cors_origins contains '*'. This creates a CSRF vulnerability. "
                "Specify explicit origins instead."
            )
        if not self.cors_origins:
            if not self.debug:
                logger.warning(
                    "CORS configuration warning: cors_allow_credentials is True but "
                    "cors_origins is empty. This will block all cross-origin requests. "
                    "Configure CORS_ORIGINS environment variable with specific origins."
                )
    return self
```



### Warning Logging

- Use Python's standard `logging` module
- Log level: `WARNING` for insecure configurations
- Include actionable guidance in log messages

### Documentation Updates

- Replace the current CORS section with comprehensive examples
- Add a "CORS Security Best Practices" subsection
- Include troubleshooting section for common CORS issues
- Show environment variable format examples

## Files to Modify

1. `app/config.py` - Change default, add validation, add logging
2. `docs/SECURITY.md` - Update CORS section with production examples and environment variable documentation

## Testing Considerations

After implementation, verify:

- Default configuration (empty origins) works correctly
- Validation prevents wildcard + credentials combination
- Warning logs appear for insecure configurations
- Documentation provides clear guidance

## Security Impact