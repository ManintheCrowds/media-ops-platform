# Educational System Service

A comprehensive educational content management and delivery system that integrates with existing self-hosted services (BookStack, Gitea, Seafile, Jellyfin) and provides specialized APIs for Raspberry Pi endpoints.

## Features

- **Content Management**: Create, organize, and version educational content
- **Project Tracking**: Manage educational projects with collaboration features
- **Taxonomy & Tagging**: Organize content with hierarchical taxonomy and tags
- **Service Integration**: Link content to BookStack, Gitea, Seafile, and Jellyfin
- **Raspberry Pi Support**: Lightweight APIs and offline sync for Pi devices
- **Progress Tracking**: Monitor user progress through educational content
- **Assessment Tools**: Create and manage quizzes and assignments

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

Once the service is running, visit:
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

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

## License

This project integrates with the main self-hosted platform.
