---
name: Database Connection Pooling
overview: Create a centralized database module with connection pooling configuration and migrate all database-related code from app/auth/oauth2.py to the new app/database.py module.
todos:
  - id: add-pool-config
    content: Add database pool configuration fields (db_pool_size, db_max_overflow, db_pool_pre_ping) to app/config.py Settings class
    status: completed
  - id: create-database-module
    content: Create app/database.py with engine creation using pool configuration, SessionLocal, and get_db() function
    status: completed
  - id: update-oauth2
    content: Update app/auth/oauth2.py to remove database setup code and import from app.database
    status: completed
  - id: update-services-import
    content: Update app/api/services.py to import get_db from app.database
    status: completed
  - id: update-health-import
    content: Update app/api/health.py to import get_db from app.database
    status: completed
  - id: update-gateway-import
    content: Update app/api/gateway.py to import get_db from app.database
    status: completed
  - id: update-tests-import
    content: Update tests/conftest.py to import get_db from app.database
    status: completed
---

# Database Connection Pooling Implementation

## Overview

Centralize database connection management by creating `app/database.py` with proper connection pooling configuration, following the pattern used in `security-service` and `education-service`. This will prevent connection exhaustion and improve database performance.

## Current State Analysis

**Current Issues:**

- `app/auth/oauth2.py` (line 24) creates engine without pooling: `create_engine(settings.database_url)`
- Database setup is mixed with authentication logic
- No connection pool configuration
- `get_db()` function is defined in `app/auth/oauth2.py` but used across multiple modules

**Files Using `get_db`:**

- `app/api/services.py` (line 8)
- `app/api/health.py` (line 9)
- `app/api/gateway.py` (line 8)
- `tests/conftest.py` (line 16)

**Reference Implementation:**

- `security-service/security_service/database.py` shows proper setup with `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`
- `education-service/app/database.py` follows the same pattern

## Implementation Steps

### 1. Add Pool Configuration to Settings

**File:** `app/config.py`Add database pool configuration fields to the `Settings` class:

- `db_pool_size: int = 10` (default pool size)
- `db_max_overflow: int = 20` (max overflow connections)
- `db_pool_pre_ping: bool = True` (enable connection health checks)

These should be configurable via environment variables (e.g., `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_PRE_PING`).

### 2. Create Centralized Database Module

**File:** `app/database.py` (new file)Create a new module that:

- Imports `Base` from `app.models` (to maintain compatibility)
- Creates engine with pooling configuration from settings:
  ```python
        engine = create_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=settings.db_pool_pre_ping
        )
  ```




- Creates `SessionLocal` sessionmaker
- Defines `get_db()` function (moved from `app/auth/oauth2.py`)
- Exports `engine`, `SessionLocal`, and `get_db` for use in other modules

### 3. Update app/auth/oauth2.py

**File:** `app/auth/oauth2.py`Changes:

- Remove lines 12-13 (sqlalchemy imports for engine/sessionmaker)
- Remove lines 23-25 (engine and SessionLocal creation)
- Remove lines 28-34 (`get_db()` function)
- Add import: `from app.database import get_db, engine`
- Update line 173 in `init_database()` to use imported `engine`

Keep all other functionality intact (OAuth2, password hashing, user management).

### 4. Update Import Statements

Update all files that import `get_db` from `app.auth.oauth2`:**File:** `app/api/services.py`

- Change line 8: `from app.database import get_db`
- Keep `get_current_user` import from `app.auth.oauth2`

**File:** `app/api/health.py`

- Change line 9: `from app.database import get_db`
- Keep `get_current_user` import from `app.auth.oauth2`

**File:** `app/api/gateway.py`

- Change line 8: `from app.database import get_db`
- Keep `get_current_user` import from `app.auth.oauth2`

### 5. Update Test Configuration

**File:** `tests/conftest.py`

- Change line 16: `from app.database import get_db`
- Keep `get_password_hash` import from `app.auth.oauth2`

Note: Tests use their own test database engine, so the pooling configuration won't affect test isolation.

## Architecture Benefits

1. **Centralized Management**: Single source of truth for database configuration
2. **Connection Pooling**: Prevents connection exhaustion under load
3. **Health Checks**: `pool_pre_ping=True` ensures stale connections are detected and replaced
4. **Configurability**: Pool settings can be adjusted via environment variables for different environments
5. **Separation of Concerns**: Database logic separated from authentication logic
6. **Consistency**: Matches the pattern used in other services (`security-service`, `education-service`)

## Configuration Example

Environment variables for production:

```bash
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_PRE_PING=True
```



## Testing Considerations

- Existing tests should continue to work as they override `get_db` dependency
- No changes needed to test database setup (tests use SQLite with separate engine)
- Integration tests will benefit from proper connection pooling

## Files to Modify

1. `app/config.py` - Add pool configuration settings
2. `app/database.py` - **NEW FILE** - Centralized database setup
3. `app/auth/oauth2.py` - Remove database setup, import from `app.database`
4. `app/api/services.py` - Update import