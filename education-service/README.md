# Educational System Service

A comprehensive educational content management and delivery system that integrates with existing self-hosted services (BookStack, Gitea, Seafile, Jellyfin) and provides specialized APIs for Raspberry Pi endpoints.

## Features

### Content Management
- **Create, organize, and version educational content**
  - Rich text content creation
  - File attachments and media
  - Content versioning and history
  - Content organization with folders and categories
- **Taxonomy & Tagging**: Organize content with hierarchical taxonomy and tags
  - Multi-level taxonomy support
  - Tag-based filtering and search
  - Content relationships and linking

### Project Management
- **Project Tracking**: Manage educational projects with collaboration features
  - Project creation and management
  - Task assignment and tracking
  - Team collaboration tools
  - Project timelines and milestones

### Service Integration
- **BookStack Integration**: Link to BookStack pages and books
  - Direct links to BookStack content
  - Content synchronization
  - Cross-platform content references
- **Gitea Integration**: Link to Git repositories
  - Repository references
  - Code examples and tutorials
  - Version control integration
- **Seafile Integration**: Link to file storage
  - File and folder references
  - Document sharing
  - Media file access
- **Jellyfin Integration**: Link to media content
  - Video and audio references
  - Streaming content integration
  - Media library access

### Raspberry Pi Support
- **Lightweight APIs**: Optimized endpoints for Pi devices
  - Reduced payload sizes
  - Efficient data formats
  - Minimal resource usage
- **Offline Sync**: Offline content synchronization
  - Content package downloads
  - Local caching
  - Background sync when online

### Learning Management
- **Progress Tracking**: Monitor user progress through educational content
  - Completion tracking
  - Time spent metrics
  - Learning path progression
  - Achievement badges
- **Assessment Tools**: Create and manage quizzes and assignments
  - Multiple choice questions
  - Short answer questions
  - Assignment submission
  - Grading and feedback

## Quick Start

### Prerequisites

- Docker and Docker Compose
- PostgreSQL 15+
- Python 3.11+ (for local development)

### Installation

1. **Set up environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

2. **Start with Docker Compose:**
```bash
docker-compose up -d
```

3. **Run migrations:**
```bash
docker exec -it platform-education alembic upgrade head
```

4. **Access the service:**
- API: http://localhost:8003
- Docs: http://localhost:8003/docs

### Service Dependencies

The education service integrates with:
- **PostgreSQL**: Primary database
- **Platform API**: Authentication and service registry
- **BookStack** (optional): Wiki/documentation integration
- **Gitea** (optional): Git repository integration
- **Seafile** (optional): File storage integration
- **Jellyfin** (optional): Media server integration

### Environment Configuration

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://education:password@education-db:5432/education

# Platform Integration
PLATFORM_API_URL=http://platform-api:8000
PLATFORM_API_KEY=your-platform-api-key

# Service Integrations (optional)
BOOKSTACK_URL=http://bookstack:80
BOOKSTACK_API_KEY=your-bookstack-key
GITEA_URL=http://gitea:3000
GITEA_TOKEN=your-gitea-token
SEAFILE_URL=http://seafile:8000
SEAFILE_API_KEY=your-seafile-key
JELLYFIN_URL=http://jellyfin:8096
JELLYFIN_API_KEY=your-jellyfin-key

# Pi Client Configuration
PI_CLIENT_ENABLED=true
PI_SYNC_INTERVAL=3600  # seconds
PI_PACKAGE_MAX_SIZE=500000000  # bytes
```

### Local Development

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up database:**
```bash
# Start PostgreSQL
docker-compose up -d education-db

# Run migrations
alembic upgrade head
```

4. **Run the service:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

### Interactive Documentation

Once the service is running, visit:
- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc
- **OpenAPI Spec**: http://localhost:8003/openapi.json

### Key API Endpoints

**Content Management:**
- `GET /api/v1/content` - List all content
- `POST /api/v1/content` - Create new content
- `GET /api/v1/content/{id}` - Get content details
- `PUT /api/v1/content/{id}` - Update content
- `DELETE /api/v1/content/{id}` - Delete content

**Projects:**
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{id}` - Get project details

**Pi-Specific Endpoints:**
- `GET /api/v1/pi/content` - Lightweight content list for Pi
- `GET /api/v1/pi/content/{id}` - Get content package for offline use
- `POST /api/v1/pi/sync` - Sync progress from Pi device
- `GET /api/v1/pi/devices/{device_id}` - Get device status

**Progress Tracking:**
- `GET /api/v1/progress` - Get user progress
- `POST /api/v1/progress` - Update progress
- `GET /api/v1/progress/stats` - Get progress statistics

**Assessments:**
- `GET /api/v1/assessments` - List assessments
- `POST /api/v1/assessments` - Create assessment
- `POST /api/v1/assessments/{id}/submit` - Submit assessment

### Example API Usage

**Create Content:**
```bash
curl -X POST "http://localhost:8003/api/v1/content" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Introduction to Python",
    "content": "Python is a programming language...",
    "tags": ["python", "programming", "beginner"],
    "category_id": 1
  }'
```

**Get Pi Content Package:**
```bash
curl -X GET "http://localhost:8003/api/v1/pi/content/123" \
  -H "Authorization: Bearer <token>" \
  -o content-package.zip
```

## Project Structure

```
education-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── database.py             # Database setup
│   ├── dependencies.py         # Dependency injection
│   ├── api/                    # API routes
│   ├── models/                 # Database models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic
│   └── auth/                   # Authentication
├── alembic/                    # Database migrations
├── tests/                      # Test suite
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Platform Integration

The education service integrates with the main platform:

- **Service Registry**: Registers with platform API
- **Authentication**: Uses platform JWT tokens
- **Health Monitoring**: Exposes health endpoint for platform monitoring
- **Metrics**: Prometheus metrics available to monitoring stack

### Service Registration

Register the education service with the platform:

```bash
curl -X POST http://localhost:8000/api/services \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "education-service",
    "service_type": "education",
    "base_url": "http://education-service:8003",
    "health_check_url": "http://education-service:8003/health",
    "requires_auth": true
  }'
```

## Deployment

### Docker Compose Deployment

The service is included in the main platform docker-compose.yml:

```bash
# Start education service
docker-compose up -d education-service education-db

# Run migrations
docker exec -it platform-education alembic upgrade head

# Check logs
docker logs -f platform-education
```

### Production Deployment

1. **Set up environment variables** in `.env` or environment
2. **Run database migrations**: `alembic upgrade head`
3. **Start service**: `docker-compose up -d education-service`
4. **Register with platform**: Use service registry API
5. **Configure monitoring**: Add to Prometheus scrape configs
6. **Set up backups**: Configure database backups

### Health Checks

The service exposes health endpoints:
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health with dependencies

## Related Services

- [Platform API](../README.md) - Main integration layer
- [Pi Client](../pi-client/README.md) - Raspberry Pi integration
- [Monitoring Stack](../monitoring/README.md) - Prometheus, Grafana

## Troubleshooting

### Service won't start

- Check database connection: `DATABASE_URL`
- Verify PostgreSQL is running
- Check required environment variables
- Review logs: `docker logs platform-education`

### Migrations fail

- Ensure database exists
- Check database user permissions
- Verify connection string format
- Review migration logs

### Pi client not connecting

- Verify `PI_CLIENT_ENABLED=true`
- Check Pi device authentication
- Review Pi-specific endpoint logs
- Test API connectivity from Pi device

### Service integrations not working

- Verify service URLs are correct
- Check API keys/tokens are valid
- Review integration logs
- Test service connectivity manually

## License

This project integrates with the main self-hosted platform.







