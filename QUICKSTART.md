# Quick Start Guide

Get your self-hosted platform up and running in minutes!

## Prerequisites

- Docker Desktop (or Docker + Docker Compose)
- 4GB+ RAM available
- 20GB+ free disk space

## Step 1: Setup

```bash
# Copy environment file
cp .env.example .env

# Edit .env and set the REQUIRED secrets (MANDATORY!)
# ⚠️ WARNING: The application will NOT start without these variables set.
# At minimum, you MUST set:
# - SECRET_KEY (must be at least 32 characters)
# - JWT_SECRET_KEY (must be at least 32 characters)

# Generate secure secrets:
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

## Step 2: Start Services

```bash
# Start all services
docker-compose up -d

# Watch the logs
docker-compose logs -f
```

Wait for all services to start (this may take a few minutes on first run).

## Step 3: Initialize Database

```bash
# Initialize the database
docker exec -it platform-api curl -X POST http://localhost:8000/api/auth/init-db
```

Or if the above doesn't work:

```bash
# Access the platform container
docker exec -it platform-api bash

# Run Python to initialize
python -c "
from platform.models import Base
from platform.config import settings
from sqlalchemy import create_engine

engine = create_engine(settings.database_url)
Base.metadata.create_all(bind=engine)
print('Database initialized')
"
```

## Step 4: Create Admin User

```bash
# Register a user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "YourSecurePassword123!"
  }'
```

## Step 5: Make User Admin

```bash
# Connect to PostgreSQL
docker exec -it platform-postgres psql -U platform -d platform

# Make user admin
UPDATE users SET is_admin = true WHERE username = 'admin';

# Exit
\q
```

## Step 6: Access Dashboard

Open your browser and navigate to:

```
http://localhost/dashboard
```

Login with your admin credentials.

## Registering Services

After logging in, you can register services through the API or directly in the database.

### Example: Register Seafile

```bash
# Get your auth token first
TOKEN=$(curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=YourSecurePassword123!" \
  | jq -r '.access_token')

# Register Seafile service
curl -X POST http://localhost:8000/api/services \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "seafile",
    "service_type": "file_storage",
    "base_url": "http://seafile:8000",
    "api_url": "http://seafile:8000/api2",
    "health_check_url": "http://seafile:8000/api2/ping/",
    "requires_auth": true
  }'
```

## Service URLs

Once services are running, you can access them directly:

- **Platform Dashboard**: http://localhost/dashboard
- **Seafile**: http://localhost/seafile
- **Jellyfin**: http://localhost/jellyfin
- **Gitea**: http://localhost/gitea
- **Grafana**: http://localhost/grafana
- **Vaultwarden**: http://localhost/vaultwarden

## Troubleshooting

### Application fails to start - missing secrets

If you see errors about `SECRET_KEY` or `JWT_SECRET_KEY` being missing or too short:

```bash
# Check platform logs for specific error
docker-compose logs platform

# Verify your .env file has the required variables set
# Both SECRET_KEY and JWT_SECRET_KEY must be at least 32 characters

# Generate and set secrets:
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

**Error messages you might see:**
- `Field required [type=missing, input_value=None, input_type=NoneType]` - Secret not set
- `Secret must be at least 32 characters long` - Secret too short

### Services won't start

```bash
# Check logs
docker-compose logs <service-name>

# Check if ports are in use
netstat -an | grep LISTEN  # Linux/Mac
netstat -an | findstr LISTEN  # Windows
```

### Database connection errors

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres
```

### Can't access dashboard

1. Check if platform service is running: `docker-compose ps platform`
2. Check platform logs: `docker-compose logs platform`
3. Verify port 80 is not in use by another service

### Reset everything

```bash
# Stop and remove all containers and volumes
docker-compose down -v

# Start fresh
docker-compose up -d
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [API.md](API.md) for API usage
- Configure service-specific settings in `.env`
- Set up SSL/TLS for production use

## Getting Help

- Check service-specific documentation
- Review Docker logs for errors
- Ensure all environment variables are set correctly
- Verify disk space and memory availability


