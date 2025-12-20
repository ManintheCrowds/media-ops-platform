---
name: Service Token Encryption
overview: Implement encryption for service authentication tokens stored in the database using Fernet symmetric encryption, with transparent encryption/decryption in the Service model and migration support for existing plain-text tokens.
todos:
  - id: create-encryption-module
    content: Create app/auth/encryption.py with encrypt_token, decrypt_token, get_encryption_key, and is_encrypted functions
    status: completed
  - id: update-service-model
    content: Update Service model in app/models/__init__.py to use hybrid_property for auth_token with automatic encryption/decryption
    status: completed
  - id: create-migration-script
    content: Create scripts/migrate_tokens.py to encrypt existing plain-text tokens in database
    status: completed
  - id: create-encryption-tests
    content: Create tests/unit/test_encryption.py with comprehensive tests for encryption/decryption functions
    status: completed
  - id: update-model-tests
    content: Update tests/unit/test_models.py to test Service model encryption/decryption behavior
    status: completed
  - id: verify-api-tests
    content: Verify and update tests/integration/test_api_services.py to ensure encrypted tokens work correctly
    status: completed
  - id: verify-gateway-tests
    content: Verify tests for app/api/gateway.py still pass with encrypted tokens
    status: completed
---

# Service Token Encryption Implementation Plan

## Overview

Implement encryption at rest for service authentication tokens using Fernet symmetric encryption. The encryption will be transparent to the application code through SQLAlchemy hybrid properties, ensuring tokens are encrypted when stored and decrypted when retrieved.

## Architecture

### Encryption Strategy

- **Library**: Use `cryptography.fernet.Fernet` (available via `python-jose[cryptography]`)
- **Key Derivation**: Derive encryption key from `app.config.settings.secret_key` using SHA-256 hashing
- **Format**: Encrypted tokens stored as base64-encoded strings in database
- **Transparency**: Use SQLAlchemy hybrid properties to handle encryption/decryption automatically

### Data Flow

```javascript
API Request → Service Model (encrypts) → Database (encrypted)
Database (encrypted) → Service Model (decrypts) → API Usage (plain text)
```



## Implementation Steps

### 1. Create Encryption Utility Module

**File**: `app/auth/encryption.py`Create encryption/decryption functions:

- `get_encryption_key(secret_key: str) -> bytes`: Derive Fernet key from secret_key using SHA-256
- `encrypt_token(token: str, secret_key: str) -> str`: Encrypt token and return base64 string
- `decrypt_token(encrypted_token: str, secret_key: str) -> str`: Decrypt token and return plain text
- `is_encrypted(value: str) -> bool`: Check if a value appears to be encrypted (for migration)

**Key Features**:

- Handle None/null tokens gracefully
- Raise custom exceptions for decryption errors
- Use Fernet for authenticated encryption (prevents tampering)

### 2. Update Service Model

**File**: `app/models/__init__.py`Modify the `Service` class to use a hybrid property for `auth_token`:

- Keep the database column as `Text` (stores encrypted value)
- Add `_auth_token_encrypted` as the actual column name (or use existing column)
- Create `@hybrid_property` for `auth_token` that:
- On get: Decrypts the stored value
- On set: Encrypts the incoming value
- Handle None values (don't encrypt None)
- Support migration: If value is not encrypted format, encrypt it on first access

**Implementation approach**:

```python
from sqlalchemy.ext.hybrid import hybrid_property
from app.auth.encryption import encrypt_token, decrypt_token, is_encrypted
from app.config import settings

class Service(Base):
    # ... existing fields ...
    _auth_token_encrypted = Column('auth_token', Text)  # Database column
    
    @hybrid_property
    def auth_token(self):
        """Get decrypted auth token."""
        if self._auth_token_encrypted is None:
            return None
        # Migration: if not encrypted, encrypt it
        if not is_encrypted(self._auth_token_encrypted):
            self._auth_token_encrypted = encrypt_token(
                self._auth_token_encrypted, 
                settings.secret_key
            )
        return decrypt_token(self._auth_token_encrypted, settings.secret_key)
    
    @auth_token.setter
    def auth_token(self, value):
        """Set encrypted auth token."""
        if value is None:
            self._auth_token_encrypted = None
        else:
            self._auth_token_encrypted = encrypt_token(value, settings.secret_key)
```



### 3. Update Services API

**File**: `app/api/services.py`No changes needed - the hybrid property handles encryption transparently. However, verify:

- `Service(**service_data.dict())` works correctly (it will)
- `setattr(service, key, value)` works correctly (it will)
- Token is never exposed in API responses (already handled - `ServiceResponse` doesn't include `auth_token`)

### 4. Update Gateway Usage

**File**: `app/api/gateway.py`No changes needed - `service.auth_token` will automatically decrypt when accessed at line 35.

### 5. Migration Strategy

**File**: `scripts/migrate_tokens.py` (new)Create a migration script to encrypt existing plain-text tokens:

- Query all services with non-null `auth_token`
- Check if token is encrypted using `is_encrypted()`
- If not encrypted, encrypt it and update the database
- Log migration progress
- Support dry-run mode

**Alternative**: Handle migration automatically in the hybrid property getter (as shown above) - simpler but less explicit.

### 6. Update Tests

**Files**:

- `tests/unit/test_models.py`
- `tests/integration/test_api_services.py`
- `tests/unit/test_encryption.py` (new)

**Test Coverage**:

- Encryption/decryption functions work correctly
- Service model encrypts on set, decrypts on get
- None tokens handled correctly
- Migration of plain-text tokens works
- Encrypted tokens are not exposed in API responses
- Gateway uses decrypted tokens correctly
- Error handling for corrupted encrypted data

### 7. Update Documentation

**File**: `docs/SECURITY.md` or similar (if exists)Document:

- Token encryption at rest
- Key derivation method
- Migration process
- Security considerations

## Security Considerations

1. **Key Management**: Encryption key derived from `secret_key` - ensure this is strong and kept secret
2. **Backward Compatibility**: Migration handles existing plain-text tokens
3. **Error Handling**: Failed decryption should log error and return None (don't crash)
4. **Token Exposure**: Ensure `ServiceResponse` model never includes `auth_token` (already verified)

## Risk Assessment

- **Risk Level**: Medium
- **Impact**: High (security improvement)
- **Rollback**: Can disable encryption by reverting Service model changes
- **Testing**: Critical - test encryption/decryption thoroughly before deployment

## Files to Modify

1. `app/auth/encryption.py` - New file
2. `app/models/__init__.py` - Modify Service class
3. `app/api/services.py` - Verify no changes needed (transparent)
4. `app/api/gateway.py` - Verify no changes needed (transparent)