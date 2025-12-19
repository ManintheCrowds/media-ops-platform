---
name: Educational System Framework
overview: Design and implement a separate microservice for an intelligent digital educational system that integrates with existing self-hosted services (BookStack, Gitea, Seafile, Jellyfin) and provides specialized APIs for Raspberry Pi endpoints. The initial prototype will focus on content management with extensibility for future features.
todos:
  - id: setup_project
    content: Create education-service project structure with FastAPI, SQLAlchemy, and Alembic configuration
    status: completed
  - id: database_schema
    content: "Implement database schema with core models: organizations, projects, content_items, taxonomy, tags, and versioning tables"
    status: completed
  - id: auth_integration
    content: Implement JWT token validation with main platform API for authentication
    status: completed
  - id: content_crud
    content: Build content management API endpoints (CRUD operations, versioning, hierarchical structure)
    status: completed
  - id: taxonomy_tagging
    content: Implement taxonomy tree and tagging system with content relationships
    status: completed
  - id: project_management
    content: Create project management API with project-content relationships
    status: completed
  - id: service_integration
    content: Build integration clients for BookStack, Gitea, Seafile, and Jellyfin with content linking
    status: completed
  - id: pi_device_api
    content: Implement Raspberry Pi device management API (registration, configuration, status)
    status: completed
  - id: pi_sync_system
    content: Build content synchronization system for Pi devices (package generation, incremental sync, download endpoints)
    status: completed
  - id: pi_content_api
    content: Create lightweight content delivery API optimized for Raspberry Pi devices
    status: completed
  - id: testing
    content: Write comprehensive tests (unit, integration, API, Pi simulation)
    status: completed
  - id: documentation
    content: Create API documentation, integration guides, and deployment documentation
    status: completed
---

# Intelligent Digital Educati

onal System Architecture

## Overview

This framework provides a comprehensive educational content management and delivery system that integrates with existing self-hosted services. It will be built as a separate FastAPI microservice that communicates with the main platform API for authentication and service discovery.

## Architecture Design

### System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WebUI[Web Dashboard]
        MobileApp[Mobile App]
        PiClient[Raspberry Pi Client]
    end
    
    subgraph "Platform Layer"
        MainPlatform[Main Platform API<br/>Authentication & Service Registry]
        EduService[Educational System Service<br/>FastAPI Microservice]
    end
    
    subgraph "Educational Service Components"
        ContentAPI[Content Management API]
        ProjectAPI[Project Tracking API]
        ProgressAPI[Progress Tracking API]
        AssessmentAPI[Assessment API]
        RecommendationEngine[Recommendation Engine]
        PiAPI[Raspberry Pi API]
    end
    
    subgraph "Data Layer"
        EduDB[(PostgreSQL<br/>Educational Database)]
        SearchIndex[(Elasticsearch/Search Index)]
        Cache[(Redis Cache)]
    end
    
    subgraph "Integrated Services"
        BookStack[BookStack<br/>Documentation]
        Gitea[Gitea<br/>Repositories]
        Seafile[Seafile<br/>File Storage]
        Jellyfin[Jellyfin<br/>Media Streaming]
    end
    
    WebUI --> MainPlatform
    MobileApp --> MainPlatform
    PiClient --> PiAPI
    MainPlatform --> EduService
    EduService --> ContentAPI
    EduService --> ProjectAPI
    EduService --> ProgressAPI
    EduService --> AssessmentAPI
    EduService --> RecommendationEngine
    EduService --> PiAPI
    ContentAPI --> EduDB
    ContentAPI --> SearchIndex
    ContentAPI --> Cache
    EduService --> BookStack
    EduService --> Gitea
    EduService --> Seafile
    EduService --> Jellyfin
```



### Service Communication Flow

```mermaid
sequenceDiagram
    participant Client
    participant MainPlatform
    participant EduService
    participant BookStack
    participant Seafile
    participant PiDevice
    
    Client->>MainPlatform: Authenticate (JWT)
    MainPlatform-->>Client: JWT Token
    Client->>EduService: Request Content (Bearer Token)
    EduService->>MainPlatform: Validate Token
    MainPlatform-->>EduService: User Info
    EduService->>EduService: Query Local DB
    EduService->>BookStack: Fetch Related Docs
    EduService->>Seafile: Fetch Media Files
    EduService-->>Client: Aggregated Content
    
    PiDevice->>EduService: Request Offline Content
    EduService->>EduService: Generate Sync Package
    EduService-->>PiDevice: Compressed Content Bundle
```



## Database Schema

### Core Tables

**organizations**

- `id` (PK, Integer)
- `name` (String, unique)
- `slug` (String, unique, indexed)
- `description` (Text)
- `settings` (JSONB) - organization-specific config
- `created_at`, `updated_at` (DateTime)

**projects**

- `id` (PK, Integer)
- `organization_id` (FK to organizations)
- `name` (String)
- `slug` (String, indexed)
- `description` (Text)
- `status` (Enum: draft, active, archived)
- `metadata` (JSONB) - project-specific data
- `created_by` (FK to users via platform)
- `created_at`, `updated_at` (DateTime)

**content_items**

- `id` (PK, Integer)
- `project_id` (FK to projects)
- `content_type` (Enum: lesson, video, document, assessment, project_template)
- `title` (String, indexed)
- `slug` (String, indexed)
- `description` (Text)
- `body` (Text) - main content
- `metadata` (JSONB) - content-specific data
- `external_refs` (JSONB) - references to BookStack/Gitea/Seafile/Jellyfin
- `version` (Integer) - for versioning
- `parent_id` (FK to content_items) - for hierarchical content
- `created_by` (FK to users)
- `created_at`, `updated_at` (DateTime)

**content_versions**

- `id` (PK, Integer)
- `content_item_id` (FK to content_items)
- `version_number` (Integer)
- `title`, `body`, `metadata` (snapshot of content)
- `created_by` (FK to users)
- `created_at` (DateTime)

**tags**

- `id` (PK, Integer)
- `name` (String, unique, indexed)
- `category` (String) - e.g., "subject", "grade_level", "skill"
- `created_at` (DateTime)

**content_tags** (many-to-many)

- `content_item_id` (FK to content_items)
- `tag_id` (FK to tags)

**taxonomy_nodes**

- `id` (PK, Integer)
- `name` (String)
- `slug` (String, indexed)
- `parent_id` (FK to taxonomy_nodes) - for hierarchical taxonomy
- `level` (Integer) - depth in hierarchy
- `metadata` (JSONB)

**content_taxonomy** (many-to-many)

- `content_item_id` (FK to content_items)
- `taxonomy_node_id` (FK to taxonomy_nodes)

**user_progress**

- `id` (PK, Integer)
- `user_id` (String) - reference to platform user
- `content_item_id` (FK to content_items)
- `status` (Enum: not_started, in_progress, completed)
- `progress_percentage` (Float)
- `last_accessed` (DateTime)
- `completed_at` (DateTime, nullable)
- `metadata` (JSONB) - progress-specific data

**assessments**

- `id` (PK, Integer)
- `content_item_id` (FK to content_items)
- `assessment_type` (Enum: quiz, assignment, project)
- `questions` (JSONB) - question data
- `grading_rubric` (JSONB)
- `settings` (JSONB) - time limits, attempts, etc.
- `created_by` (FK to users)
- `created_at`, `updated_at` (DateTime)

**assessment_submissions**

- `id` (PK, Integer)
- `assessment_id` (FK to assessments)
- `user_id` (String)
- `answers` (JSONB)
- `score` (Float, nullable)
- `status` (Enum: draft, submitted, graded)
- `submitted_at` (DateTime, nullable)
- `graded_at` (DateTime, nullable)

**collaboration_sessions**

- `id` (PK, Integer)
- `content_item_id` (FK to content_items)
- `session_type` (Enum: edit, review, discussion)
- `participants` (JSONB) - array of user IDs
- `active_users` (JSONB) - currently active
- `created_at`, `updated_at` (DateTime)

**recommendations**

- `id` (PK, Integer)
- `user_id` (String)
- `content_item_id` (FK to content_items)
- `recommendation_type` (Enum: content_based, collaborative, trending)
- `score` (Float) - recommendation strength
- `reason` (Text) - why recommended
- `created_at` (DateTime)

**pi_devices**

- `id` (PK, Integer)
- `device_id` (String, unique, indexed)
- `device_name` (String)
- `device_type` (Enum: kiosk, interactive, sync, iot)
- `organization_id` (FK to organizations)
- `last_sync` (DateTime)
- `sync_status` (Enum: synced, syncing, error)
- `capabilities` (JSONB) - device capabilities
- `settings` (JSONB) - device configuration
- `created_at`, `updated_at` (DateTime)

**pi_sync_packages**

- `id` (PK, Integer)
- `device_id` (FK to pi_devices)
- `package_type` (Enum: full, incremental, content_only)
- `content_ids` (JSONB) - array of content item IDs
- `package_url` (String) - download URL
- `package_size` (BigInteger)
- `checksum` (String)
- `created_at` (DateTime)
- `expires_at` (DateTime)

## API Specifications

### Core Content Management API

**Base Path**: `/api/v1/education`

#### Content Endpoints

- `GET /content` - List content items (with filtering, pagination, search)
- `GET /content/{id}` - Get specific content item
- `POST /content` - Create new content item
- `PUT /content/{id}` - Update content item
- `DELETE /content/{id}` - Delete content item
- `GET /content/{id}/versions` - List content versions
- `POST /content/{id}/versions` - Create new version
- `GET /content/{id}/versions/{version}` - Get specific version
- `POST /content/{id}/revert/{version}` - Revert to version

#### Project Endpoints

- `GET /projects` - List projects
- `GET /projects/{id}` - Get project details
- `POST /projects` - Create project
- `PUT /projects/{id}` - Update project
- `GET /projects/{id}/content` - List content in project

#### Taxonomy & Tagging

- `GET /taxonomy` - Get taxonomy tree
- `GET /tags` - List tags (with filtering)
- `POST /content/{id}/tags` - Add tags to content
- `DELETE /content/{id}/tags/{tag_id}` - Remove tag

#### Search & Discovery

- `GET /search` - Full-text search across content
- `GET /content/{id}/related` - Get related content
- `GET /recommendations` - Get personalized recommendations

### Raspberry Pi API

**Base Path**: `/api/v1/pi`

#### Device Management

- `POST /devices/register` - Register new Pi device
- `GET /devices/{device_id}` - Get device info
- `PUT /devices/{device_id}` - Update device config
- `GET /devices/{device_id}/status` - Get sync status

#### Content Synchronization

- `GET /devices/{device_id}/sync/check` - Check for updates
- `POST /devices/{device_id}/sync/request` - Request sync package
- `GET /devices/{device_id}/sync/packages/{package_id}/download` - Download package
- `POST /devices/{device_id}/sync/complete` - Mark sync complete

#### Content Delivery (Lightweight)

- `GET /devices/{device_id}/content` - Get content list for device
- `GET /devices/{device_id}/content/{id}` - Get content item (optimized format)
- `GET /devices/{device_id}/content/{id}/media` - Stream media file
- `GET /devices/{device_id}/display/config` - Get display configuration

#### Offline Capability

- `GET /devices/{device_id}/offline/manifest` - Get offline content manifest
- `POST /devices/{device_id}/offline/activity` - Submit offline activity data
- `GET /devices/{device_id}/offline/queue` - Get queued sync operations

#### IoT Integration

- `POST /devices/{device_id}/sensors/data` - Submit sensor data
- `GET /devices/{device_id}/sensors/config` - Get sensor configuration
- `GET /devices/{device_id}/sensors/data` - Query sensor data

### Integration API

**Base Path**: `/api/v1/integrations`

- `POST /bookstack/link` - Link content to BookStack page
- `POST /gitea/link` - Link content to Gitea repository
- `POST /seafile/link` - Link content to Seafile library
- `POST /jellyfin/link` - Link content to Jellyfin media
- `GET /external/{service}/{external_id}` - Fetch external resource

## Integration Patterns

### Service Integration Architecture

```mermaid
graph LR
    subgraph "Educational Service"
        ContentManager[Content Manager]
        IntegrationLayer[Integration Layer]
    end
    
    subgraph "External Services"
        BookStack[BookStack API]
        Gitea[Gitea API]
        Seafile[Seafile API]
        Jellyfin[Jellyfin API]
    end
    
    ContentManager --> IntegrationLayer
    IntegrationLayer --> BookStack
    IntegrationLayer --> Gitea
    IntegrationLayer --> Seafile
    IntegrationLayer --> Jellyfin
```



### Integration Service Clients

Create integration clients similar to existing service clients:

- `services/integrations/bookstack_client.py` - BookStack API client
- `services/integrations/gitea_client.py` - Gitea API client (extend existing)
- `services/integrations/seafile_client.py` - Seafile API client (extend existing)
- `services/integrations/jellyfin_client.py` - Jellyfin API client (extend existing)

### Content Linking Strategy

Store external references in `content_items.external_refs` JSONB field:

```json
{
  "bookstack": {"page_id": 123, "book_id": 45},
  "gitea": {"repo_id": 67, "branch": "main"},
  "seafile": {"library_id": "abc", "file_path": "/docs/lesson1.pdf"},
  "jellyfin": {"item_id": "xyz", "media_type": "video"}
}
```



## Prototype Implementation Plan

### Phase 1: Foundation (Weeks 1-2)

1. **Project Setup**

- Create new FastAPI service in `education-service/`
- Set up database models using SQLAlchemy
- Configure Alembic for migrations
- Set up Docker container for service

2. **Database Schema**

- Implement core models: organizations, projects, content_items
- Create initial Alembic migration
- Set up database indexes for performance

3. **Authentication Integration**

- Create service to validate JWT tokens with main platform
- Implement dependency injection for authenticated users
- Add role-based access control (RBAC)

### Phase 2: Content Management (Weeks 3-4)

4. **Content CRUD API**

- Implement content item endpoints
- Add content versioning system
- Implement hierarchical content structure
- Add content search using PostgreSQL full-text search

5. **Taxonomy & Tagging**

- Implement taxonomy tree structure
- Add tagging system
- Create content-tag and content-taxonomy relationships

6. **Project Management**

- Implement project CRUD operations
- Add project-content relationships
- Create project templates

### Phase 3: Service Integration (Week 5)

7. **External Service Integration**

- Create integration clients for BookStack, Gitea, Seafile, Jellyfin
- Implement content linking functionality
- Add external resource fetching
- Create unified content aggregation

### Phase 4: Raspberry Pi API (Week 6)

8. **Pi Device Management**

- Implement device registration
- Add device configuration management
- Create device capability detection

9. **Content Synchronization**

- Design sync package format (compressed bundle)
- Implement sync package generation
- Add incremental sync support
- Create download endpoints

10. **Lightweight Content API**

    - Optimize content responses for Pi devices
    - Implement media streaming endpoints
    - Add display configuration API

### Phase 5: Testing & Documentation (Week 7)

11. **Testing**

    - Unit tests for core functionality
    - Integration tests for service clients
    - API endpoint tests
    - Pi device simulation tests

12. **Documentation**

    - API documentation (OpenAPI/Swagger)
    - Integration guide
    - Pi device setup guide
    - Deployment documentation

## File Structure

```javascript
education-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── dependencies.py         # Dependency injection
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── content.py          # Content endpoints
│   │   ├── projects.py          # Project endpoints
│   │   ├── taxonomy.py         # Taxonomy endpoints
│   │   ├── search.py           # Search endpoints
│   │   ├── pi/
│   │   │   ├── __init__.py
│   │   │   ├── devices.py      # Device management
│   │   │   ├── sync.py         # Sync endpoints
│   │   │   ├── content.py      # Pi content API
│   │   │   └── iot.py          # IoT endpoints
│   │   └── integrations.py     # Integration endpoints
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── organization.py
│   │   ├── project.py
│   │   ├── content.py
│   │   ├── taxonomy.py
│   │   ├── progress.py
│   │   ├── assessment.py
│   │   └── pi_device.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── content.py          # Pydantic schemas
│   │   ├── project.py
│   │   └── pi.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── content_service.py
│   │   ├── project_service.py
│   │   ├── search_service.py
│   │   ├── recommendation_service.py
│   │   ├── sync_service.py
│   │   └── integrations/
│   │       ├── __init__.py
│   │       ├── bookstack_client.py
│   │       ├── gitea_client.py
│   │       ├── seafile_client.py
│   │       └── jellyfin_client.py
│   │
│   └── auth/
│       ├── __init__.py
│       └── platform_auth.py   # JWT validation with main platform
│
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docker-compose.yml          # Service-specific compose
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```



## Key Implementation Details

### Authentication Flow

The educational service validates JWT tokens by calling the main platform's token validation endpoint or sharing JWT secret:

```python
# app/auth/platform_auth.py
async def validate_platform_token(token: str) -> UserInfo:
    # Option 1: Call main platform API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PLATFORM_URL}/api/auth/validate",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()
    
    # Option 2: Validate locally with shared secret
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    return UserInfo(**payload)
```



### Content Versioning

Implement Git-like versioning:

- Each update creates a new version record
- Versions are immutable
- Support branching for collaborative editing
- Merge capabilities for conflict resolution

### Sync Package Format

For Raspberry Pi offline sync:

- Compressed tar.gz or zip archive
- Manifest JSON with content metadata
- Optimized media files (compressed images, lower bitrate videos)
- Incremental updates (only changed content)

### Search Implementation

Initial: PostgreSQL full-text search with `tsvector`Future: Elasticsearch integration for advanced search

### Recommendation Engine

Initial: Simple content-based filtering

- Tag similarity
- Taxonomy proximity
- User progress patterns

Future: Machine learning-based recommendations

## Docker Integration

Add to main `docker-compose.yml`:

```yaml
education-service:
  build: ./education-service
  container_name: platform-education
  environment:
    - DATABASE_URL=postgresql://education:password@education-db:5432/education
    - PLATFORM_URL=http://platform:8000
    - JWT_SECRET_KEY=${JWT_SECRET_KEY}
  ports:
    - "8003:8000"
  depends_on:
    - education-db
    - platform
  networks:
    - platform-network

education-db:
  image: postgres:15
  container_name: platform-education-db
  environment:
    - POSTGRES_USER=education
    - POSTGRES_PASSWORD=password
    - POSTGRES_DB=education
  volumes:
    - education_db_data:/var/lib/postgresql/data
  networks:
    - platform-network
```



## Next Steps After Prototype

1. **Progress Tracking**: User progress monitoring and analytics
2. **Assessment System**: Quiz/assignment creation and grading
3. **Collaboration**: Real-time collaborative editing
4. **Advanced Recommendations**: ML-based content recommendations
5. **Analytics Dashboard**: Learning analytics and insights
6. **Mobile App**: Native mobile applications
7. **Advanced Pi Features**: IoT sensor integration, display management

## Success Metrics

- Content items created and managed
- API response times (< 200ms for content queries)
- Pi device sync success rate