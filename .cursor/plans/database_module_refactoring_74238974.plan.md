---
name: Database Module Refactoring
overview: Create a shared database module (app/database.py) to centralize database configuration and eliminate duplicate engine/SessionLocal creation in app/auth/oauth2.py. Update all API files to use the shared get_db dependency.
todos:
  - id: create-database-module
    content: Create app/database.py with shared engine, SessionLocal, get_db(), and init_db() functions
    status: completed
  - id: update-oauth2
    content: Update app/auth/oauth2.py to remove duplicate database setup and import from app.database
    status: completed
  - id: update-services-api
    content: Update app/api/services.py to import get_db from app.database
    status: completed
  - id: update-health-api
    content: Update app/api/health.py to import get_db from app.database
    status: completed
  - id: update-gateway-api
    content: Update app/api/gateway.py to import get_db from app.database
    status: completed
---

# Database Module Refactoring Plan

## Current State

- `app/auth/oauth2.py` creates its own engine and SessionLocal (lines 24-25)
- `app/api/services.py`, `app/api/health.py`, and `app/api/gateway.py` import `get_db` from `app.auth.oauth2`
- This creates duplicate database connections and potential connection pool issues
- Other services (security-service, education-service) have proper centralized database modules

## Implementation Steps

### 1. Create `app/database.py`

Create a new shared database module following the pattern used in security-service and education-service:

- Import `Base` from `app.models` (already defined there)
- Create engine with connection pooling:
- `pool_pre_ping=True` (verify connections before using)
- `pool_size=10` (maintain 10 connections)
- `max_overflow=20` (allow up to 20 additional connections)
- Create `SessionLocal` factory
- Implement `get_db()` dependency function (generator pattern for FastAPI)
- Implement `init_db()` function that:
- Imports all models from `app.models` to ensure they're registered
- Calls `Base.metadata.create_all(bind=engine)`

### 2. Update `app/auth/oauth2.py`

- Remove lines 12-13 (imports of `create_engine` and `sessionmaker`)
- Remove lines 24-25 (engine and SessionLocal creation)
- Remove lines 28-34 (get_db function)
- Add import: `from app.database import get_db, engine`
- Update `init_database()` endpoint (line 173) to use shared `init_db()` function from `app.database`

### 3. Update API Files

Update imports in:

- `app/api/services.py` (line 8): Change `from app.auth.oauth2 import get_current_user, get_db` to import `get_db` from `app.database`
- `app/api/health.py` (line 9): Same change
- `app/api/gateway.py` (line 8): Same change

### 4. Verify Dependencies

Ensure `get_current_user` is still imported correctly in all API files (it should remain from `app.auth.oauth2`)

## Files to Modify

1. **Create**: `app/database.py` - New shared database module
2. **Update**: `app/auth/oauth2.py` - Remove duplicate setup, import from shared module
3. **Update**: `app/api/services.py` - Update import statement
4. **Update**: `app/api/health.py` - Update import statement  
5. **Update**: `app/api/gateway.py` - Update import statement

## Benefits

- Single source of truth for database configuration
- Proper connection pooling prevents connection exhaustion
- Consistent database setup across the application