# AI Codebase Map - Navigation Guide

**Purpose**: Quick reference guide for AI agents to understand the codebase structure, key directories, files, common tasks, and where to locate or add specific code.

**How to Use This Map**: 
- Use the directory structure to find where code lives
- Use "Common Tasks" sections to find file locations for specific operations
- Use "Decision Points" to determine where to place new code
- Use "Quick Reference Table" for fast lookups

**Codebase Overview**: This is a FastAPI-based self-hosted platform integration that provides unified authentication and API gateway for multiple services (Seafile, Jellyfin, Gitea, etc.).

**Related Documents**:
- [AI_PATTERNS.md](AI_PATTERNS.md) - Code patterns to follow
- [AI_TASK_TEMPLATES.md](AI_TASK_TEMPLATES.md) - Task decomposition
- [AI_VALIDATION_CHECKLIST.md](AI_VALIDATION_CHECKLIST.md) - Validation requirements

---

## Section 1: Directory Structure Overview

```
software/
├── app/                    # Core FastAPI application
│   ├── main.py            # Application entry point
│   ├── config.py          # Application configuration
│   ├── api/               # API routes
│   ├── auth/              # Authentication modules
│   └── models/            # Database models
├── services/               # Service client implementations
│   ├── file_storage/      # Seafile client
│   ├── media_server/      # Jellyfin client
│   ├── productivity/      # BookStack client
│   ├── dev_tools/         # Gitea client
│   ├── monitoring/        # Prometheus/Grafana clients
│   └── security/          # Vaultwarden client
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── e2e/               # End-to-end tests
│   └── fixtures/          # Test fixtures
├── frontend/              # Web UI
├── docs/                  # Documentation
├── scripts/               # Utility scripts
│   ├── automation/       # Deployment and automation
│   ├── monitoring/       # Monitoring scripts
│   ├── network/           # Network configuration
│   └── pi/                # Raspberry Pi management
├── nginx/                 # Nginx configuration
├── monitoring/            # Monitoring configuration
├── docker-compose.yml     # Docker Compose configuration
├── requirements.txt       # Python dependencies
└── README.md             # Project documentation
```

### Purpose of Each Top-Level Directory

- **`app/`**: Core application code (FastAPI routes, models, auth)
- **`services/`**: External service client implementations
- **`tests/`**: Test suite organized by test type
- **`frontend/`**: Web UI (HTML, CSS, JavaScript)
- **`docs/`**: Project documentation
- **`scripts/`**: Utility and automation scripts
- **`nginx/`**: Reverse proxy configuration
- **`monitoring/`**: Monitoring stack configuration

### Key Conventions

- **Service clients**: `services/{service_name}/client.py` and `config.py`
- **API routes**: `app/api/{feature}.py`
- **Database models**: `app/models/__init__.py`
- **Tests**: `tests/{unit|integration|e2e}/test_{feature}.py`
- **Configuration**: Pydantic `BaseSettings` classes

---

## Section 2: Core Application (`app/`)

### Purpose and Responsibility

The `app/` directory contains the core FastAPI application, including routes, authentication, database models, and configuration.

### Key Files and Their Purposes

| File | Purpose | When to Modify |
|------|---------|----------------|
| `main.py` | FastAPI app initialization, route registration | Adding new routers, middleware |
| `config.py` | Application settings (Pydantic BaseSettings) | Adding new configuration options |
| `api/gateway.py` | Service proxy endpoints | Adding new service endpoints |
| `api/services.py` | Service registry management | Service CRUD operations |
| `api/health.py` | Health check endpoints | Health check logic |
| `auth/oauth2.py` | OAuth2 authentication | Authentication logic |
| `auth/jwt_handler.py` | JWT token handling | Token generation/validation |
| `models/__init__.py` | SQLAlchemy database models | Adding new models, modifying schemas |

### Common Patterns

- **Router Pattern**: Each feature has its own router in `app/api/`
- **Dependency Injection**: Use FastAPI `Depends()` for database and auth
- **Error Handling**: Use `HTTPException` with appropriate status codes

### Common Tasks with File Locations

| Task | File Location |
|------|---------------|
| Add new API endpoint | `app/api/{feature}.py` or add to existing router |
| Add authentication | `app/auth/oauth2.py` |
| Add database model | `app/models/__init__.py` |
| Add configuration | `app/config.py` |
| Register new router | `app/main.py` |

---

## Section 3: Service Clients (`services/`)

### Structure Pattern

Each service follows this structure:

```
services/
└── {service_name}/
    ├── __init__.py
    ├── config.py          # Pydantic BaseSettings configuration
    └── {service}_client.py  # Service client implementation
```

### Key Patterns

1. **Configuration Class** (`config.py`):
   - Extends `pydantic_settings.BaseSettings`
   - Uses `env_prefix` for environment variables
   - Provides defaults

2. **Client Class** (`{service}_client.py`):
   - Implements async context manager
   - Has `ping()` method for health checks
   - Uses `httpx.AsyncClient` for HTTP requests

3. **Async Context Manager**: All clients support `async with Client()`

### Common Tasks

| Task | File Location |
|------|---------------|
| Add new service client | `services/{service_name}/client.py` |
| Add service configuration | `services/{service_name}/config.py` |
| Update service client | `services/{service_name}/{service}_client.py` |

### Existing Services List

| Service | Directory | Client File | Description |
|---------|-----------|-------------|-------------|
| Seafile | `services/file_storage/` | `seafile_client.py` | File storage and sync |
| Jellyfin | `services/media_server/` | `jellyfin_client.py` | Media server |
| BookStack | `services/productivity/` | `wiki_client.py` | Wiki/documentation |
| Gitea | `services/dev_tools/` | `gitea_client.py` | Git service |
| Prometheus | `services/monitoring/` | `prometheus_client.py` | Metrics collection |
| Grafana | `services/monitoring/` | `grafana_client.py` | Visualization |
| Vaultwarden | `services/security/` | `vaultwarden_client.py` | Password manager |

---

## Section 4: API Gateway (`app/api/gateway.py`)

### Purpose

The gateway provides unified endpoints that proxy requests to various services, abstracting service-specific details from clients.

### Key Patterns

1. **Service Lookup**: Query database for active service by type
2. **Client Usage**: Use service client with async context manager
3. **Error Handling**: Return 404 if service not found, 502 if service unavailable
4. **Authentication**: All endpoints require authentication via `get_current_user`

### Common Tasks

| Task | File Location | Pattern |
|------|---------------|---------|
| Add service endpoint | `app/api/gateway.py` | Query service, use client, return data |
| Add generic proxy | `app/api/gateway.py` | Use `proxy_request()` helper |

### Integration Points

- **Database**: Queries `Service` model for service registry
- **Service Clients**: Uses clients from `services/` directory
- **Authentication**: Uses `get_current_user` from `app/auth/oauth2.py`

---

## Section 5: Tests (`tests/`)

### Structure

```
tests/
├── conftest.py           # Shared fixtures and configuration
├── unit/                 # Unit tests (isolated, mocked)
├── integration/          # Integration tests (with database)
├── e2e/                  # End-to-end tests (full workflows)
└── fixtures/             # Test data and mocks
```

### Patterns

1. **Mocking**: Use `respx` for HTTP mocking in unit tests
2. **Fixtures**: Shared fixtures in `conftest.py`
3. **Markers**: Use `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`
4. **Test Database**: SQLite for speed in tests

### Common Tasks

| Task | File Location |
|------|---------------|
| Add unit test | `tests/unit/test_{feature}.py` |
| Add integration test | `tests/integration/test_{feature}.py` |
| Add E2E test | `tests/e2e/test_{workflow}.py` |
| Add test fixture | `tests/conftest.py` or `tests/fixtures/` |
| Add mock data | `tests/fixtures/mock_responses.py` |

### Test Organization Principles

- **Unit tests**: Test individual functions/classes in isolation
- **Integration tests**: Test components working together (with database)
- **E2E tests**: Test complete user workflows
- **Fixtures**: Reusable test data and mocks

---

## Section 6: Documentation (`docs/`)

### Key Documents and Their Purposes

| Document | Purpose | When to Update |
|----------|---------|----------------|
| `ARCHITECTURE.md` | System architecture | Architecture changes |
| `DEVELOPMENT.md` | Development setup | Development process changes |
| `DEPLOYMENT.md` | Deployment procedures | Deployment changes |
| `SECURITY.md` | Security practices | Security updates |
| `AI_PRINCIPLES.md` | AI agent principles | Principle changes |
| `AI_PATTERNS.md` | Code patterns | New patterns emerge |
| `AI_TASK_TEMPLATES.md` | Task templates | New task types |
| `AI_VALIDATION_CHECKLIST.md` | Validation checklists | New validation requirements |
| `AI_CODEBASE_MAP.md` | This document | Codebase structure changes |
| `AI_PROMPT_LIBRARY.md` | Prompt templates | New prompts needed |
| `AI_DOCUMENTATION_INDEX.md` | Navigation hub | New AI docs added |

### Documentation Standards

- Markdown format
- Clear structure with headers
- Code examples where applicable
- Cross-references to related docs
- Last updated date

### Cross-Reference Maintenance

When updating documentation:
1. Identify all cross-references
2. Update links if content moved
3. Verify links work
4. Update "See Also" sections

---

## Section 7: Scripts (`scripts/`)

### Structure by Category

```
scripts/
├── automation/           # Deployment and automation scripts
│   ├── backup.sh        # Backup operations
│   ├── deploy.sh        # Deployment
│   ├── rollback.sh      # Rollback operations
│   └── ...
├── monitoring/           # Monitoring scripts
│   └── cursor-*.ps1     # Cursor connection monitoring
├── network/              # Network configuration
│   └── pfsense-*.sh     # pfSense configuration
└── pi/                   # Raspberry Pi management
    └── pi-*.sh           # Pi fleet management
```

### Key Scripts and Their Purposes

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `automation/backup.sh` | Create backups | Before changes |
| `automation/rollback.sh` | Rollback changes | After failed deployment |
| `automation/deploy.sh` | Deploy services | Deployment |
| `register_default_services.py` | Register services | Initial setup |
| `test_services.py` | Test service connections | Testing |

### Common Tasks

| Task | Script Location |
|------|-----------------|
| Create backup | `scripts/automation/backup.sh` |
| Deploy service | `scripts/automation/deploy.sh` |
| Rollback | `scripts/automation/rollback.sh` |
| Test services | `scripts/test_services.py` |

---

## Section 8: Configuration Files

### Key Config Files

| File | Purpose | When to Modify |
|------|---------|----------------|
| `docker-compose.yml` | Service orchestration | Adding/removing services |
| `nginx/nginx.conf` | Reverse proxy config | Adding routes, upstreams |
| `.env.example` | Environment variable template | Adding new env vars |
| `requirements.txt` | Python dependencies | Adding/updating packages |
| `pytest.ini` | Pytest configuration | Test configuration |
| `.cursorrules` | Cursor AI rules | AI agent behavior |

### Configuration Patterns

- **Environment Variables**: Use `.env` file, reference in Pydantic `BaseSettings`
- **Docker Compose**: Define services, networks, volumes
- **Nginx**: Define upstreams and location blocks

---

## Section 9: Integration Points

### Where Services Connect

1. **API Gateway** (`app/api/gateway.py`):
   - Queries database for services
   - Uses service clients
   - Returns unified responses

2. **Service Registry** (`app/models/__init__.py` - `Service` model):
   - Stores service configuration
   - Tracks service health
   - Manages service metadata

3. **Service Clients** (`services/{service_name}/`):
   - Connect to external services
   - Handle authentication
   - Provide unified interface

### Data Flow Diagrams

```
Client Request
    ↓
Nginx (nginx/nginx.conf)
    ↓
FastAPI App (app/main.py)
    ↓
API Gateway (app/api/gateway.py)
    ↓
Service Client (services/{service}/client.py)
    ↓
External Service
```

### Service Registry

Services are registered in the database (`Service` model) and can be:
- Added via API (`app/api/services.py`)
- Added via script (`scripts/register_default_services.py`)
- Managed via admin interface

---

## Section 10: Common Modification Patterns

### Adding New Service (Step-by-Step)

1. **Create Service Directory**: `services/{service_name}/`
2. **Create Config**: `services/{service_name}/config.py` (Pydantic BaseSettings)
3. **Create Client**: `services/{service_name}/{service}_client.py` (async context manager, ping())
4. **Add Gateway Route**: `app/api/gateway.py` (query service, use client)
5. **Update Docker Compose**: `docker-compose.yml` (add service container)
6. **Update Nginx**: `nginx/nginx.conf` (add upstream and location)
7. **Write Tests**: `tests/unit/test_{service}_client.py`, `tests/integration/test_{service}_gateway.py`
8. **Update Documentation**: `docs/` or `README.md`

### Adding New API Endpoint (Step-by-Step)

1. **Create/Update Router**: `app/api/{feature}.py` or add to existing router
2. **Define Models**: Request/response Pydantic models
3. **Implement Endpoint**: Function with route decorator, auth dependency
4. **Register Router**: `app/main.py` (include router)
5. **Write Tests**: `tests/unit/test_{feature}.py`, `tests/integration/test_{feature}.py`
6. **Update Documentation**: `API.md` or OpenAPI docs

### Adding Database Model (Step-by-Step)

1. **Define Model**: `app/models/__init__.py` (SQLAlchemy model with timestamps)
2. **Create Migration**: `alembic revision --autogenerate -m "Add {model}"`
3. **Review Migration**: Check generated migration script
4. **Test Migration**: Apply in test environment, test up and down
5. **Update Code**: Use model in application code
6. **Write Tests**: `tests/unit/test_models.py`

---

## Section 11: Decision Points

### Table: "Where to Put New Code" by Type

| Code Type | Location | Example |
|-----------|----------|---------|
| **API Endpoint** | `app/api/{feature}.py` | `app/api/gateway.py` |
| **Database Model** | `app/models/__init__.py` | `User`, `Service` models |
| **Service Client** | `services/{service_name}/client.py` | `services/file_storage/seafile_client.py` |
| **Configuration** | `{module}/config.py` | `app/config.py`, `services/{service}/config.py` |
| **Authentication** | `app/auth/` | `app/auth/oauth2.py` |
| **Business Logic** | `app/services/` (if exists) or `app/api/` | Service-specific logic |
| **Tests** | `tests/{unit|integration|e2e}/test_{feature}.py` | `tests/unit/test_service_clients.py` |
| **Scripts** | `scripts/{category}/` | `scripts/automation/backup.sh` |
| **Documentation** | `docs/` | `docs/ARCHITECTURE.md` |

### Decision Tree for Code Placement

```
Is it an API endpoint?
├─ Yes → app/api/{feature}.py
└─ No → Is it a database model?
    ├─ Yes → app/models/__init__.py
    └─ No → Is it a service client?
        ├─ Yes → services/{service_name}/client.py
        └─ No → Is it configuration?
            ├─ Yes → {module}/config.py
            └─ No → Is it a test?
                ├─ Yes → tests/{type}/test_{feature}.py
                └─ No → Is it a script?
                    ├─ Yes → scripts/{category}/
                    └─ No → Review with team
```

---

## Section 12: Key Conventions

### Naming Conventions

- **Files**: `snake_case.py` (e.g., `seafile_client.py`)
- **Classes**: `PascalCase` (e.g., `SeafileClient`)
- **Functions**: `snake_case` (e.g., `get_libraries()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Database tables**: `snake_case` (e.g., `users`, `services`)

### Import Organization

```python
# Standard library
import asyncio
from typing import Optional, Dict, List

# Third-party
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Local
from app.models import User
from app.auth.oauth2 import get_current_user
from services.file_storage.seafile_client import SeafileClient
```

### Code Organization Principles

1. **Separation of Concerns**: API routes, business logic, data access separated
2. **Dependency Injection**: Use FastAPI `Depends()` for dependencies
3. **Async/Await**: Use async for I/O operations
4. **Type Hints**: Always include type hints
5. **Error Handling**: Use appropriate exceptions and HTTP status codes

---

## Section 13: Quick Reference Table

### "Need to... Go to..." Lookup Table

| Need to... | Go to... |
|------------|----------|
| Add API endpoint | `app/api/{feature}.py` |
| Add database model | `app/models/__init__.py` |
| Add service client | `services/{service_name}/client.py` |
| Add configuration | `{module}/config.py` |
| Add authentication | `app/auth/oauth2.py` |
| Add test | `tests/{unit|integration|e2e}/test_{feature}.py` |
| Add script | `scripts/{category}/` |
| Update Docker config | `docker-compose.yml` |
| Update Nginx config | `nginx/nginx.conf` |
| Register service | `app/api/services.py` or `scripts/register_default_services.py` |
| Find service client | `services/{service_name}/client.py` |
| Find API route | `app/api/{feature}.py` |
| Find database model | `app/models/__init__.py` |
| Find test fixtures | `tests/conftest.py` or `tests/fixtures/` |

---

## Section 14: Anti-Patterns

### Where NOT to Put Code

- ❌ **Don't put business logic in `main.py`** → Use `app/api/` or `app/services/`
- ❌ **Don't put service clients in `app/`** → Use `services/` directory
- ❌ **Don't put API routes in service client files** → Use `app/api/`
- ❌ **Don't put database models in API files** → Use `app/models/`
- ❌ **Don't put tests in source code directories** → Use `tests/` directory

### Common Mistakes in Code Placement

1. **Mixing concerns**: Putting API logic in service clients
2. **Wrong directory**: Putting service code in `app/` instead of `services/`
3. **Missing structure**: Not following established directory patterns
4. **Inconsistent naming**: Not following naming conventions

---

## See Also

- [AI_PATTERNS.md](AI_PATTERNS.md) - Code patterns to follow
- [AI_TASK_TEMPLATES.md](AI_TASK_TEMPLATES.md) - Task decomposition with file locations
- [AI_VALIDATION_CHECKLIST.md](AI_VALIDATION_CHECKLIST.md) - Validation requirements
- [AI_PRINCIPLES.md](AI_PRINCIPLES.md) - Core principles

---

**Last Updated**: 2024-01-01  
**Maintained By**: Project Team  
**Review Cycle**: Quarterly
