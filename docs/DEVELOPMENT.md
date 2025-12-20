# Development Guide

## Getting Started

### Prerequisites

- Python 3.10 or 3.11
- PostgreSQL 15+ (or Docker)
- Docker and Docker Compose (optional)
- Git

### Development Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd software
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment:**
```bash
cp .env.example .env
# Edit .env with your development settings
```

5. **Start PostgreSQL (if not using Docker):**
```bash
# Using Docker
docker-compose up -d postgres

# Or install PostgreSQL locally and create database
createdb platform
```

6. **Initialize database:**
```bash
# Set DEBUG=True in .env
python -c "from app.main import app; from app.models import Base; from app.config import settings; from sqlalchemy import create_engine; engine = create_engine(settings.database_url); Base.metadata.create_all(bind=engine)"
```

7. **Run the application:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Project Structure

```
software/
├── app/                    # Main application
│   ├── main.py            # FastAPI app entry point
│   ├── config.py          # Configuration
│   ├── api/               # API routes
│   ├── auth/              # Authentication
│   └── models/            # Database models
├── services/              # Service clients
│   ├── file_storage/      # Seafile client
│   ├── media_server/      # Jellyfin client
│   ├── productivity/      # BookStack client
│   ├── dev_tools/         # Gitea client
│   ├── monitoring/        # Prometheus/Grafana clients
│   └── security/         # Vaultwarden client
├── frontend/              # Web UI
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
├── docs/                  # Documentation
└── scripts/               # Utility scripts
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit
pytest tests/integration
pytest tests/e2e

# Run with coverage
pytest --cov=app --cov=services --cov-report=html

# Run specific test file
pytest tests/unit/test_auth_jwt.py

# Run with markers
pytest -m "unit"
pytest -m "integration"
pytest -m "not slow"
```

### Code Quality

```bash
# Format code
black app services tests

# Lint code
flake8 app services

# Type checking
mypy app

# Security scan
bandit -r app services
```

### Database Migrations

**Important**: The `/api/auth/init-db` endpoint is deprecated and should not be used in production. Use Alembic migrations instead.

#### Using Alembic (Recommended)

Alembic provides version-controlled database migrations, which is the recommended approach for managing database schema changes:

```bash
# Initialize Alembic (if not already initialized)
alembic init alembic

# Configure alembic.ini and alembic/env.py
# Set sqlalchemy.url in alembic.ini or use environment variable

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration file in alembic/versions/
# Edit if needed to customize the migration

# Apply migration
alembic upgrade head

# Rollback migration (if needed)
alembic downgrade -1
```

**Setting up Alembic for the first time:**

1. Install Alembic (if not already installed):
   ```bash
   pip install alembic
   ```

2. Initialize Alembic in the project root:
   ```bash
   alembic init alembic
   ```

3. Configure `alembic/env.py`:
   ```python
   from app.config import settings
   from app.models import Base
   
   # Set the database URL
   config.set_main_option("sqlalchemy.url", settings.database_url)
   
   # Set target metadata
   target_metadata = Base.metadata
   ```

4. Import all models in `alembic/env.py` so Alembic can detect them:
   ```python
   from app.models import User, Service
   ```

5. Create initial migration:
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   ```

6. Apply migration:
   ```bash
   alembic upgrade head
   ```

**Example migration workflow:**

```bash
# 1. Make changes to models in app/models/
# 2. Generate migration
alembic revision --autogenerate -m "Add new column to User model"

# 3. Review generated migration file
# 4. Apply migration
alembic upgrade head

# 5. If something goes wrong, rollback
alembic downgrade -1
```

#### Deprecated: /init-db Endpoint

The `/api/auth/init-db` endpoint is **deprecated** and will be removed in a future version. It is only available when:

- `ENABLE_DEBUG_ENDPOINTS=True` is set in environment
- User is authenticated as admin
- IP address is in whitelist (if `DEBUG_ENDPOINT_ALLOWED_IPS` is configured)

**Security Note**: This endpoint should never be enabled in production. Use Alembic migrations instead for all database schema management.

## Adding a New Service

### Step 1: Create Service Client

1. Create service directory:
```bash
mkdir -p services/new_service
```

2. Create `config.py`:
```python
from pydantic_settings import BaseSettings

class NewServiceConfig(BaseSettings):
    base_url: str = "http://new-service:8000"
    api_token: Optional[str] = None
    
    class Config:
        env_file = ".env"
```

3. Create client:
```python
# services/new_service/new_service_client.py
import httpx
from typing import Optional, Dict, List, Any
from services.new_service.config import NewServiceConfig

class NewServiceClient:
    def __init__(self, config: Optional[NewServiceConfig] = None):
        self.config = config or NewServiceConfig()
        self.base_url = self.config.base_url.rstrip('/')
        # ... implementation
```

### Step 2: Add Gateway Route

In `app/api/gateway.py`:
```python
@router.get("/new-service/endpoint")
async def get_new_service_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = db.query(Service).filter(
        Service.service_type == "new_service",
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    async with NewServiceClient() as client:
        data = await client.get_data()
        return {"data": data}
```

### Step 3: Update Docker Compose

Add service to `docker-compose.yml`:
```yaml
new-service:
  image: new-service:latest
  container_name: platform-new-service
  # ... configuration
```

### Step 4: Add Tests

Create test file:
```python
# tests/unit/test_new_service_client.py
@pytest.mark.unit
class TestNewServiceClient:
    # ... tests
```

## Code Style

### Python Style Guide

- Follow PEP 8
- Use type hints
- Maximum line length: 120 characters
- Use Black for formatting
- Use descriptive variable names

### Example

```python
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/endpoint")
async def get_data(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get data with limit."""
    # Implementation
    return {"data": []}
```

## Testing Guidelines

### Unit Tests

- Test individual functions/methods
- Mock external dependencies
- Fast execution (< 1 second per test)
- High coverage target (80%+)

### Integration Tests

- Test API endpoints
- Use test database
- Test database operations
- Test service integrations

### E2E Tests

- Test complete workflows
- Use real service mocks
- Test user journeys
- Mark as `@pytest.mark.slow`

### Writing Tests

```python
@pytest.mark.unit
class TestFeature:
    def test_feature_success(self, fixture):
        """Test successful case."""
        result = feature_function()
        assert result == expected
    
    def test_feature_failure(self, fixture):
        """Test failure case."""
        with pytest.raises(ExpectedException):
            feature_function()
```

## Debugging

### Local Development

1. Enable debug mode in `.env`:
```
DEBUG=True
```

2. Use debugger:
```python
import pdb; pdb.set_trace()
# Or use IDE breakpoints
```

3. View logs:
```bash
# Application logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f platform
```

### Common Issues

**Database connection errors:**
- Check DATABASE_URL in .env
- Verify PostgreSQL is running
- Check network connectivity

**Import errors:**
- Verify virtual environment is activated
- Check PYTHONPATH
- Reinstall dependencies

**Service client errors:**
- Verify service URLs
- Check service is running
- Verify API tokens

## Contributing

### Pull Request Process

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Ensure all tests pass: `pytest`
5. Format code: `black app services tests`
6. Commit changes: `git commit -m "Add new feature"`
7. Push to branch: `git push origin feature/new-feature`
8. Create Pull Request

### Commit Messages

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `chore:` Maintenance

Example:
```
feat: Add new service client for ExampleService

- Implement ExampleServiceClient
- Add gateway routes
- Add unit tests
- Update documentation
```

### Code Review Guidelines

- All code must have tests
- Code must pass linting
- Documentation must be updated
- Follow existing patterns
- Consider performance implications

## Documentation

### Writing Documentation

- Use clear, concise language
- Include code examples
- Update when code changes
- Add diagrams for complex flows

### API Documentation

FastAPI automatically generates OpenAPI docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Performance Considerations

- Use async/await for I/O operations
- Implement connection pooling
- Cache frequently accessed data
- Optimize database queries
- Monitor performance metrics

## Security Best Practices

- Never commit secrets
- Use environment variables
- Validate all inputs
- Sanitize user data
- Use parameterized queries
- Implement rate limiting
- Regular security audits

## Code Structure Deep Dive

### Application Structure

```
app/
├── __init__.py
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration management (Pydantic Settings)
│
├── api/                    # API route handlers
│   ├── __init__.py
│   ├── gateway.py          # Service gateway endpoints
│   ├── health.py           # Health check endpoints
│   └── services.py         # Service management endpoints
│
├── auth/                   # Authentication module
│   ├── __init__.py
│   ├── oauth2.py           # OAuth2 password flow, user management
│   └── jwt_handler.py     # JWT token creation and validation
│
└── models/                 # Database models
    ├── __init__.py         # SQLAlchemy models (User, Service)
```

### Service Client Structure

```
services/
├── __init__.py
│
├── file_storage/          # File storage service integration
│   ├── __init__.py
│   ├── config.py          # SeafileConfig (Pydantic Settings)
│   └── seafile_client.py  # SeafileClient (async context manager)
│
├── media_server/          # Media server integration
│   ├── __init__.py
│   ├── config.py          # JellyfinConfig
│   └── jellyfin_client.py # JellyfinClient
│
├── productivity/          # Productivity tools
│   ├── __init__.py
│   ├── config.py          # WikiConfig
│   └── wiki_client.py     # WikiClient
│
├── dev_tools/            # Development tools
│   ├── __init__.py
│   ├── config.py          # GiteaConfig
│   └── gitea_client.py    # GiteaClient
│
├── monitoring/            # Monitoring services
│   ├── __init__.py
│   ├── config.py          # PrometheusConfig, GrafanaConfig
│   ├── prometheus_client.py
│   └── grafana_client.py
│
└── security/             # Security tools
    ├── __init__.py
    ├── config.py         # VaultwardenConfig
    └── vaultwarden_client.py
```

### Design Patterns

#### 1. Service Client Pattern

All service clients follow a consistent pattern:

```python
class ServiceClient:
    """Standard service client pattern."""
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        # Initialize with config or defaults
        self.config = config or ServiceConfig()
        self._session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        # Create HTTP session with authentication
        self._session = httpx.AsyncClient(...)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Clean up session
        if self._session:
            await self._session.aclose()
    
    async def ping(self) -> bool:
        # Health check method
        pass
```

**Benefits**:
- Consistent interface across all services
- Automatic resource cleanup
- Easy to test and mock
- Type-safe configuration

#### 2. Dependency Injection Pattern

FastAPI's dependency injection is used throughout:

```python
# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication dependency
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    # Validate token and return user
    pass

# Usage in routes
@router.get("/endpoint")
async def endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Use dependencies
    pass
```

**Benefits**:
- Automatic dependency resolution
- Easy to test (can override dependencies)
- Clean separation of concerns
- Reusable dependencies

#### 3. Repository Pattern (Implicit)

Service registry acts as a repository:

```python
# Service lookup by type
service = db.query(Service).filter(
    Service.service_type == "file_storage",
    Service.is_active == True
).first()

# Service lookup by name
service = db.query(Service).filter(
    Service.name == "seafile",
    Service.is_active == True
).first()
```

#### 4. Gateway Pattern

API Gateway routes requests to appropriate services:

```python
@router.get("/file-storage/libraries")
async def get_libraries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Lookup service
    service = db.query(Service).filter(...).first()
    
    # 2. Initialize client
    async with ServiceClient() as client:
        # 3. Call service
        data = await client.get_libraries()
        # 4. Return formatted response
        return {"libraries": data}
```

**Benefits**:
- Single entry point for all services
- Unified authentication
- Request/response transformation
- Service abstraction

## Testing Strategy

### Test Pyramid

```
        /\
       /E2E\          Few, slow, comprehensive
      /------\
     /Integration\    Some, medium speed
    /------------\
   /    Unit      \   Many, fast, isolated
  /----------------\
```

### Unit Tests

**Purpose**: Test individual functions/methods in isolation

**Characteristics**:
- Fast execution (< 1 second per test)
- No external dependencies
- Mock all external calls
- High coverage target (80%+)

**Example**:
```python
@pytest.mark.unit
class TestJWTHandler:
    def test_create_token(self):
        """Test JWT token creation."""
        token = create_access_token({"sub": "user"})
        assert token is not None
        assert isinstance(token, str)
    
    def test_verify_token(self):
        """Test JWT token verification."""
        token = create_access_token({"sub": "user"})
        payload = verify_token(token)
        assert payload["sub"] == "user"
```

### Integration Tests

**Purpose**: Test components working together

**Characteristics**:
- Use test database
- Test API endpoints
- Test database operations
- Medium speed (1-5 seconds per test)

**Example**:
```python
@pytest.mark.integration
class TestAuthAPI:
    def test_register_user(self, client, db):
        """Test user registration."""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        assert response.json()["username"] == "testuser"
    
    def test_login(self, client, db, test_user):
        """Test user login."""
        response = client.post("/api/auth/token", data={
            "username": "testuser",
            "password": "password123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
```

### E2E Tests

**Purpose**: Test complete user workflows

**Characteristics**:
- Test full workflows
- Use real service mocks
- Slow execution (5+ seconds per test)
- Mark as `@pytest.mark.slow`

**Example**:
```python
@pytest.mark.e2e
@pytest.mark.slow
class TestServiceWorkflow:
    async def test_service_registration_workflow(self, client, admin_token):
        """Test complete service registration workflow."""
        # 1. Register service
        response = client.post("/api/services", ...)
        service_id = response.json()["id"]
        
        # 2. Check health
        response = client.get(f"/api/health/services/{service_id}")
        assert response.json()["status"] == "healthy"
        
        # 3. Use gateway
        response = client.get("/api/gateway/file-storage/libraries")
        assert response.status_code == 200
```

### Test Fixtures

**Common Fixtures** (`tests/conftest.py`):

```python
@pytest.fixture
def db():
    """Database session fixture."""
    # Create test database
    # Yield session
    # Cleanup
    pass

@pytest.fixture
def client(db):
    """FastAPI test client."""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db):
    """Create test user."""
    user = User(username="testuser", ...)
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def admin_token(client, admin_user):
    """Get admin authentication token."""
    response = client.post("/api/auth/token", ...)
    return response.json()["access_token"]
```

### Mocking External Services

```python
@pytest.fixture
def mock_seafile(httpx_mock):
    """Mock Seafile API responses."""
    httpx_mock.add_response(
        method="GET",
        url="http://seafile:80/api2/repos/",
        json=[{"id": "repo1", "name": "Library 1"}]
    )
    return httpx_mock

def test_get_libraries(mock_seafile):
    """Test library retrieval with mocked service."""
    async with SeafileClient() as client:
        libraries = await client.get_libraries()
        assert len(libraries) == 1
```

### Test Coverage

**Target Coverage**:
- Overall: 80%+
- Critical paths: 95%+
- Service clients: 75%+
- API endpoints: 90%+

**Generate Coverage Report**:
```bash
pytest --cov=app --cov=services --cov-report=html
open htmlcov/index.html
```

## Code Style Guide

### Python Style

- Follow PEP 8
- Use Black for formatting (line length: 120)
- Use type hints for all functions
- Maximum line length: 120 characters

### Naming Conventions

- **Classes**: PascalCase (`ServiceClient`, `UserResponse`)
- **Functions/Methods**: snake_case (`get_libraries`, `create_service`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Variables**: snake_case (`service_id`, `current_user`)
- **Private**: Prefix with underscore (`_session`, `_internal_method`)

### Type Hints

Always use type hints:

```python
from typing import Optional, List, Dict, Any

def get_service(
    service_id: int,
    db: Session
) -> Optional[Service]:
    """Get service by ID."""
    return db.query(Service).filter(Service.id == service_id).first()

async def get_libraries() -> List[Dict[str, Any]]:
    """Get libraries from service."""
    # Implementation
    return []
```

### Docstrings

Use Google-style docstrings:

```python
def get_service(service_id: int, db: Session) -> Optional[Service]:
    """Get service by ID.
    
    Args:
        service_id: The ID of the service to retrieve
        db: Database session
        
    Returns:
        Service object if found, None otherwise
        
    Raises:
        HTTPException: If service not found
    """
    pass
```

### Error Handling

Always handle errors gracefully:

```python
async def get_data(self) -> List[Dict[str, Any]]:
    """Get data with error handling."""
    try:
        response = await self._session.get("/api/endpoint")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code}")
        return []
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []
```

## Git Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: Feature branches
- `fix/*`: Bug fix branches
- `hotfix/*`: Critical production fixes

### Commit Messages

Follow Conventional Commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `chore`: Maintenance

**Example**:
```
feat(gateway): Add file storage libraries endpoint

- Implement SeafileClient integration
- Add GET /api/gateway/file-storage/libraries endpoint
- Add unit tests for SeafileClient

Closes #123
```

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-service-integration
   ```

2. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

3. **Run Tests**
   ```bash
   pytest
   black app services tests
   flake8 app services
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: Add new service integration"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/new-service-integration
   # Create PR on GitHub/GitLab
   ```

6. **Code Review**
   - Address review comments
   - Update PR as needed

7. **Merge**
   - Squash and merge (preferred)
   - Delete feature branch

## Release Process

### Version Numbering

Follow Semantic Versioning (SemVer):
- `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Steps

1. **Update Version**
   ```python
   # app/config.py
   app_version: str = "1.2.3"
   ```

2. **Update Changelog**
   - Document all changes
   - Group by type (Added, Changed, Fixed)

3. **Create Release Branch**
   ```bash
   git checkout -b release/1.2.3
   ```

4. **Final Testing**
   - Run full test suite
   - Test deployment process
   - Verify documentation

5. **Tag Release**
   ```bash
   git tag -a v1.2.3 -m "Release version 1.2.3"
   git push origin v1.2.3
   ```

6. **Merge to Main**
   ```bash
   git checkout main
   git merge release/1.2.3
   git push origin main
   ```

7. **Create GitHub Release**
   - Use tag as release
   - Include changelog
   - Attach release notes

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
