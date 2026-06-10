# AI Patterns - Code Implementation Patterns

**Purpose**: Detailed code implementation patterns with real examples from the codebase to guide AI agents in writing consistent, maintainable code.

**When to Use This Document**: 
- Writing new code
- Refactoring existing code
- Following established conventions
- Understanding code structure

**Related Documents**:
- [AI_CODEBASE_MAP.md](AI_CODEBASE_MAP.md) - Find where code lives
- [AI_TASK_TEMPLATES.md](AI_TASK_TEMPLATES.md) - Task context
- [AI_VALIDATION_CHECKLIST.md](AI_VALIDATION_CHECKLIST.md) - Validation requirements
- [AI_PRINCIPLES.md](AI_PRINCIPLES.md) - Core principles

---

## Section 1: Service Client Pattern

**Reference**: `services/file_storage/seafile_client.py`, `services/media_server/jellyfin_client.py`, `services/dev_tools/gitea_client.py`

### Complete Pattern Template

```python
"""Service API client."""

import httpx
from typing import Optional, Dict, List, Any
from services.service_name.config import ServiceConfig


class ServiceClient:
    """Client for interacting with Service API."""
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        self.config = config or ServiceConfig()
        self.base_url = self.config.base_url.rstrip('/')
        self.api_token = self.config.api_token
        self._session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Token {self.api_token}"
        
        self._session = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.aclose()
    
    async def ping(self) -> bool:
        """Check if service is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/ping")
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get a resource by ID."""
        if not self._session:
            async with self:
                return await self.get_resource(resource_id)
        
        try:
            response = await self._session.get(f"/api/resources/{resource_id}")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
```

### Key Components

1. **Configuration Class Pattern** (from `services/file_storage/config.py`):
```python
"""Configuration for service."""

from pydantic_settings import BaseSettings
from typing import Optional


class ServiceConfig(BaseSettings):
    """Service configuration."""
    
    base_url: str = "http://service:8000"
    api_token: Optional[str] = None
    
    class Config:
        env_prefix = "SERVICE_"
        case_sensitive = False
```

2. **Async Context Manager**: Always implement `__aenter__` and `__aexit__` for proper resource management.

3. **Health Check Method**: Always include a `ping()` method for health checks.

4. **Error Handling**: Use try/except blocks, return `None` or empty collections on failure.

5. **Session Management**: Use `_session` attribute, create if not exists in methods.

### Checklist for New Service Clients

- [ ] Configuration class extends `BaseSettings` with `env_prefix`
- [ ] Client class implements async context manager (`__aenter__`, `__aexit__`)
- [ ] `ping()` method implemented for health checks
- [ ] All methods handle exceptions gracefully
- [ ] Session management follows pattern (create if not exists)
- [ ] Type hints on all methods
- [ ] Docstrings for all public methods
- [ ] Base URL normalized (strip trailing slashes)

---

## Section 2: API Endpoint Pattern

**Reference**: `app/api/gateway.py`, `app/auth/oauth2.py`

### FastAPI Router Setup

```python
"""API routes for feature."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import User
from app.auth.oauth2 import get_current_user, get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/endpoint")
async def get_endpoint(
    param: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get endpoint description."""
    # Implementation
    return {"data": "result"}
```

### Authentication Dependency Pattern

```python
from app.auth.oauth2 import get_current_user, get_db
from app.models import User
from sqlalchemy.orm import Session

@router.get("/protected")
async def protected_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Protected endpoint requiring authentication."""
    # User is authenticated, use current_user
    return {"user": current_user.username}
```

### Request/Response Models

```python
from pydantic import BaseModel

class CreateRequest(BaseModel):
    """Request model for creation."""
    name: str
    description: Optional[str] = None

class CreateResponse(BaseModel):
    """Response model for creation."""
    id: int
    name: str
    created_at: datetime

@router.post("/create", response_model=CreateResponse)
async def create_item(
    request: CreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new item."""
    # Implementation
    return CreateResponse(id=1, name=request.name, created_at=datetime.now())
```

### Error Handling with HTTP Status Codes

```python
from fastapi import HTTPException, status

@router.get("/item/{item_id}")
async def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get item by ID."""
    item = db.query(Item).filter(Item.id == item_id).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )
    
    return item
```

### Gateway Endpoint Pattern (Service Proxy)

```python
@router.get("/service/resource")
async def get_service_resource(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get resource from service."""
    service = db.query(Service).filter(
        Service.service_type == "service_type",
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    async with ServiceClient() as client:
        resource = await client.get_resource()
        return {"resource": resource}
```

### Checklist for New Endpoints

- [ ] Router created with descriptive name
- [ ] Authentication dependency added if required
- [ ] Database dependency added if needed
- [ ] Request/response models defined with Pydantic
- [ ] Error handling with appropriate HTTP status codes
- [ ] Type hints on all parameters
- [ ] Docstrings for all endpoints
- [ ] Proper HTTP method used (GET, POST, PUT, DELETE)
- [ ] Response model specified in decorator if using Pydantic models

---

## Section 3: Database Model Pattern

**Reference**: `app/models/__init__.py`

### SQLAlchemy Model Structure

```python
"""Data models for the platform."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()


class ModelName(Base):
    """Model description."""
    
    __tablename__ = "table_name"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Required fields
    name = Column(String(100), nullable=False)
    
    # Optional fields
    description = Column(Text, nullable=True)
    
    # Boolean fields
    is_active = Column(Boolean, default=True)
    
    # Timestamps (always include)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Timestamp Pattern

Always include `created_at` and `updated_at`:

```python
created_at = Column(DateTime(timezone=True), server_default=func.now())
updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Index Patterns

```python
# Single column index
username = Column(String(50), unique=True, index=True, nullable=False)

# Composite index (in __table_args__)
__table_args__ = (
    Index('idx_service_type_active', 'service_type', 'is_active'),
)
```

### Foreign Key Relationships

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class ChildModel(Base):
    """Child model with foreign key."""
    
    __tablename__ = "child_table"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("parent_table.id"), nullable=False)
    
    # Relationship
    parent = relationship("ParentModel", back_populates="children")

class ParentModel(Base):
    """Parent model."""
    
    __tablename__ = "parent_table"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relationship
    children = relationship("ChildModel", back_populates="parent")
```

### Alembic Migration Pattern

When creating migrations:

```python
# alembic revision --autogenerate -m "Add new model"
def upgrade():
    op.create_table(
        'table_name',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_table_name_id'), 'table_name', ['id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_table_name_id'), table_name='table_name')
    op.drop_table('table_name')
```

### Checklist for New Models

- [ ] Extends `Base` from `declarative_base()`
- [ ] `__tablename__` defined (snake_case)
- [ ] Primary key `id` column with index
- [ ] `created_at` and `updated_at` timestamp columns
- [ ] Appropriate column types (String, Integer, Boolean, Text, DateTime)
- [ ] Indexes on frequently queried columns
- [ ] Foreign keys defined if relationships exist
- [ ] Relationships defined with `relationship()`
- [ ] Docstring for model class
- [ ] Alembic migration created

---

## Section 4: Test Pattern

**Reference**: `tests/unit/test_service_clients.py`, `tests/integration/test_api_gateway.py`, `tests/conftest.py`

### Unit Test Structure with respx Mocking

```python
"""Unit tests for service client."""

import pytest
import respx
import httpx
from services.service_name.client import ServiceClient


@pytest.mark.asyncio
class TestServiceClient:
    """Test service client."""
    
    async def test_ping_success(self):
        """Test successful ping."""
        client = ServiceClient()
        with respx.mock:
            respx.get("http://service:8000/api/ping").mock(
                return_value=httpx.Response(200)
            )
            result = await client.ping()
            assert result is True
    
    async def test_ping_failure(self):
        """Test failed ping."""
        client = ServiceClient()
        with respx.mock:
            respx.get("http://service:8000/api/ping").mock(
                return_value=httpx.Response(500)
            )
            result = await client.ping()
            assert result is False
    
    async def test_get_resource(self):
        """Test getting resource."""
        client = ServiceClient()
        mock_data = {"id": 1, "name": "test"}
        with respx.mock:
            respx.get("http://service:8000/api/resources/1").mock(
                return_value=httpx.Response(200, json=mock_data)
            )
            async with client:
                result = await client.get_resource("1")
                assert result == mock_data
```

### Integration Test Pattern

```python
"""Integration tests for API endpoints."""

import pytest
import respx
import httpx
from fastapi import status
from tests.fixtures.mock_responses import mock_service_response


@pytest.mark.integration
class TestAPIEndpoints:
    """Test API endpoints."""
    
    def test_get_endpoint(self, client, test_token, db_session):
        """Test getting endpoint."""
        # Setup test data
        from app.models import Service
        service = Service(
            name="test-service",
            service_type="service_type",
            base_url="http://test-service:8000",
            is_active=True
        )
        db_session.add(service)
        db_session.commit()
        
        # Mock external service
        mock_data = mock_service_response()
        with respx.mock:
            respx.get("http://test-service:8000/api/resource").mock(
                return_value=httpx.Response(200, json=mock_data)
            )
            
            # Make request
            response = client.get(
                "/api/endpoint",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            
            # Assertions
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "data" in data
```

### E2E Test Pattern

```python
"""E2E tests for workflows."""

import pytest
from fastapi import status


@pytest.mark.e2e
class TestWorkflows:
    """Test end-to-end workflows."""
    
    def test_complete_workflow(self, client, test_user, db_session):
        """Test complete user workflow."""
        # 1. Authenticate
        response = client.post(
            "/api/auth/token",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        assert response.status_code == status.HTTP_200_OK
        token = response.json()["access_token"]
        
        # 2. Use authenticated endpoint
        response = client.get(
            "/api/protected",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # 3. Verify state
        # Additional assertions
```

### Fixture Patterns

From `tests/conftest.py`:

```python
@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_token(test_user: User) -> str:
    """Create a JWT token for test user."""
    return create_access_token(
        data={"sub": test_user.username, "email": test_user.email},
        expires_delta=timedelta(minutes=30)
    )
```

### Test Markers and Organization

```python
# Markers in pytest.ini
[pytest]
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests

# Usage
@pytest.mark.unit
def test_unit_function():
    pass

@pytest.mark.integration
def test_integration():
    pass
```

### Checklist for New Tests

- [ ] Test class named `TestClassName`
- [ ] Test methods named `test_what_it_tests`
- [ ] Appropriate marker used (`@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`)
- [ ] `@pytest.mark.asyncio` for async tests
- [ ] External services mocked with `respx`
- [ ] Test fixtures used from `conftest.py`
- [ ] Assertions check both success and failure cases
- [ ] Edge cases covered
- [ ] Test data cleaned up (if needed)
- [ ] Docstrings for test methods

---

## Section 5: Error Handling Pattern

### Standard Exception Handling

```python
try:
    result = await operation()
    return result
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Operation failed: {str(e)}"
    )
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred"
    )
```

### HTTP Exception Patterns

```python
from fastapi import HTTPException, status

# Not found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found"
)

# Unauthorized
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication required"
)

# Forbidden
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Insufficient permissions"
)

# Bad request
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid request data"
)
```

### Logging Patterns

```python
import logging

logger = logging.getLogger(__name__)

# Info for normal operations
logger.info(f"Processing request for user {user_id}")

# Warning for recoverable issues
logger.warning(f"Service {service_name} returned unexpected status")

# Error for failures
logger.error(f"Failed to connect to service: {e}", exc_info=True)

# Debug for detailed information
logger.debug(f"Request data: {request_data}")
```

### User-Friendly Error Messages

```python
# Good: User-friendly
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="The requested file was not found. Please check the file ID and try again."
)

# Bad: Technical details exposed
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"FileNotFoundError: No file with ID {file_id} in database table 'files'"
)
```

### Error Recovery Strategies

```python
# Retry with exponential backoff
async def operation_with_retry(max_retries=3):
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
            logger.warning(f"Retry {attempt + 1}/{max_retries}")

# Fallback to default
try:
    result = await get_data()
except Exception:
    logger.warning("Failed to get data, using default")
    result = default_data
```

---

## Section 6: Configuration Pattern

**Reference**: `services/file_storage/config.py`, `app/config.py`

### Pydantic BaseSettings Pattern

```python
"""Configuration management."""

from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Application Name"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    
    # Database
    database_url: str = "postgresql://user:<POSTGRES_PASSWORD>@localhost/db"
    
    # Service URLs
    service_url: Optional[str] = "http://service:8000"
    service_api_token: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()
```

### Environment Variable Naming

- Use uppercase with underscores: `DATABASE_URL`, `SERVICE_API_TOKEN`
- Prefix service-specific vars: `SEAFILE_BASE_URL`, `JELLYFIN_API_KEY`
- Use descriptive names: `JWT_SECRET_KEY` not `SECRET`

### Default Values

Always provide sensible defaults:

```python
base_url: str = "http://localhost:8000"  # Development default
timeout: int = 30  # Seconds
max_retries: int = 3
```

### Validation

```python
from pydantic import validator

class Settings(BaseSettings):
    port: int = 8000
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
```

---

## Section 7: Documentation Pattern

### Code Docstring Standards

```python
def function_name(param1: str, param2: int) -> Dict[str, Any]:
    """Brief description of what the function does.
    
    Longer description if needed, explaining the purpose,
    behavior, and any important details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param1 is invalid
        HTTPException: When operation fails
    """
    pass
```

### Module-Level Documentation

```python
"""Module description.

This module provides functionality for [purpose].
It includes [key features].

Example:
    ```python
    from module import Class
    instance = Class()
    result = instance.method()
    ```
"""
```

### Type Hint Documentation

```python
from typing import Optional, List, Dict, Any

def process_data(
    items: List[Dict[str, Any]],  # List of item dictionaries
    filter_func: Optional[callable] = None  # Optional filter function
) -> Dict[str, Any]:  # Returns processed data dictionary
    """Process items with optional filtering."""
    pass
```

### Inline Comment Guidelines

```python
# Good: Explains why, not what
# Retry with exponential backoff to handle transient network issues
await asyncio.sleep(2 ** attempt)

# Bad: States the obvious
# Increment the counter
counter += 1
```

---

## Section 8: Common Patterns Summary Table

| Pattern | Use Case | File Location | Key Components |
|---------|----------|--------------|----------------|
| **Service Client** | External API integration | `services/{service_name}/client.py` | Async context manager, ping(), error handling |
| **API Endpoint** | FastAPI routes | `app/api/{feature}.py` | Router, auth dependency, error handling |
| **Database Model** | Data persistence | `app/models/__init__.py` | SQLAlchemy Base, timestamps, indexes |
| **Test** | Code validation | `tests/{unit|integration|e2e}/test_*.py` | pytest, respx mocking, fixtures |
| **Configuration** | Settings management | `{module}/config.py` | Pydantic BaseSettings, env vars |
| **Error Handling** | Exception management | Throughout codebase | HTTPException, logging, user messages |

---

## Section 9: Anti-Patterns

### What NOT to Do

#### ❌ Hardcoded Values

```python
# Bad
base_url = "http://localhost:8000"
api_key = "hardcoded-key-123"

# Good
base_url = config.base_url
api_key = config.api_key
```

#### ❌ Silent Failures

```python
# Bad
try:
    result = await operation()
except Exception:
    pass  # Silent failure

# Good
try:
    result = await operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise
```

#### ❌ Missing Type Hints

```python
# Bad
def process(data):
    return data.items()

# Good
def process(data: Dict[str, Any]) -> List[Any]:
    return list(data.items())
```

#### ❌ Inconsistent Error Handling

```python
# Bad: Different error handling in same module
def method1():
    try:
        # code
    except:
        return None

def method2():
    # code
    if error:
        raise Exception("Error")

# Good: Consistent pattern
def method1():
    try:
        # code
    except SpecificException as e:
        logger.error(f"Error: {e}")
        raise HTTPException(...)
```

#### ❌ Missing Docstrings

```python
# Bad
def get_data(id):
    return db.query(Model).filter(Model.id == id).first()

# Good
def get_data(id: int) -> Optional[Model]:
    """Get model by ID.
    
    Args:
        id: Model identifier
    
    Returns:
        Model instance or None if not found
    """
    return db.query(Model).filter(Model.id == id).first()
```

### Common Mistakes

1. **Not using async context managers** for service clients
2. **Missing health check methods** (`ping()`) in service clients
3. **Hardcoding URLs** instead of using configuration
4. **Not handling exceptions** in async operations
5. **Missing type hints** on function parameters and returns
6. **Inconsistent naming** (mixing snake_case and camelCase)
7. **Not using dependency injection** for database sessions
8. **Missing indexes** on frequently queried database columns

### How to Recognize Anti-Patterns

- Code that works but feels "wrong"
- Repeated code blocks (DRY violation)
- Hardcoded values that should be configurable
- Missing error handling
- Inconsistent patterns across similar code
- Missing or incomplete documentation

---

## See Also

- [AI_CODEBASE_MAP.md](AI_CODEBASE_MAP.md) - Find where to place code
- [AI_TASK_TEMPLATES.md](AI_TASK_TEMPLATES.md) - Task context and decomposition
- [AI_VALIDATION_CHECKLIST.md](AI_VALIDATION_CHECKLIST.md) - Validation requirements
- [AI_PRINCIPLES.md](AI_PRINCIPLES.md) - Core principles and governance

---

**Last Updated**: 2024-01-01  
**Maintained By**: Project Team  
**Review Cycle**: Quarterly
