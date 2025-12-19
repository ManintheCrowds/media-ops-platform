# Deployment Guide

## Prerequisites

- Docker and Docker Compose
- PostgreSQL 15+ (or use provided Docker container)
- Access to main platform API for authentication
- Network access to integrated services (BookStack, Gitea, Seafile, Jellyfin)

## Quick Start

### 1. Clone and Configure

```bash
cd education-service
cp .env.example .env
# Edit .env with your configuration
```

### 2. Update Environment Variables

Edit `.env` file:

```env
# Database
DATABASE_URL=postgresql://education:password@education-db:5432/education

# Platform Integration
PLATFORM_URL=http://platform:8000
JWT_SECRET_KEY=your-shared-jwt-secret

# Service URLs
BOOKSTACK_URL=http://bookstack:80
GITEA_URL=http://gitea:3000
SEAFILE_URL=http://seafile:8000
JELLYFIN_URL=http://jellyfin:8096
```

### 3. Start Services

```bash
docker-compose up -d
```

### 4. Run Database Migrations

```bash
docker exec -it platform-education alembic upgrade head
```

### 5. Verify Deployment

```bash
curl http://localhost:8003/health
```

Should return: `{"status": "healthy"}`

## Production Deployment

### 1. Security Configuration

**Critical**: Update all secrets in `.env`:

```bash
# Generate secure secrets
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update:
- `SECRET_KEY`
- `JWT_SECRET_KEY`
- Database passwords

### 2. Database Setup

For production, use a managed PostgreSQL database or configure the container with:
- Persistent volumes
- Regular backups
- Connection pooling

### 3. Network Configuration

Ensure the educational service can communicate with:
- Main platform API (for authentication)
- Integrated services (BookStack, Gitea, Seafile, Jellyfin)
- Database

### 4. Reverse Proxy Setup

Configure Nginx or Traefik to route requests:

```nginx
location /api/v1/education {
    proxy_pass http://education-service:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### 5. SSL/TLS

Use Let's Encrypt or your SSL certificate provider:

```nginx
server {
    listen 443 ssl;
    server_name education.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://education-service:8000;
    }
}
```

## Integration with Main Platform

### Update Main Platform docker-compose.yml

Add the educational service to the main platform's `docker-compose.yml`:

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

### Update Nginx Configuration

Add routing for educational service:

```nginx
location /api/v1/education {
    proxy_pass http://education-service:8000/api/v1/education;
}

location /api/v1/pi {
    proxy_pass http://education-service:8000/api/v1/pi;
}

location /api/v1/integrations {
    proxy_pass http://education-service:8000/api/v1/integrations;
}
```

## Database Migrations

### Create Migration

```bash
docker exec -it platform-education alembic revision --autogenerate -m "Description"
```

### Apply Migrations

```bash
docker exec -it platform-education alembic upgrade head
```

### Rollback Migration

```bash
docker exec -it platform-education alembic downgrade -1
```

## Monitoring

### Health Checks

```bash
curl http://localhost:8003/health
```

### Logs

```bash
docker logs -f platform-education
```

### Database Connection

```bash
docker exec -it platform-education-db psql -U education -d education
```

## Backup and Recovery

### Database Backup

```bash
docker exec platform-education-db pg_dump -U education education > backup.sql
```

### Database Restore

```bash
docker exec -i platform-education-db psql -U education education < backup.sql
```

## Troubleshooting

### Service Not Starting

1. Check logs: `docker logs platform-education`
2. Verify environment variables
3. Check database connectivity
4. Verify network configuration

### Authentication Issues

1. Verify `JWT_SECRET_KEY` matches main platform
2. Check `PLATFORM_URL` is accessible
3. Verify token format in requests

### Integration Failures

1. Verify service URLs are correct
2. Check API tokens/keys are valid
3. Test service connectivity from container
4. Review integration service logs

## Scaling

### Horizontal Scaling

Run multiple instances behind a load balancer:

```yaml
education-service:
  deploy:
    replicas: 3
```

### Database Optimization

- Enable connection pooling
- Add appropriate indexes
- Configure query caching
- Monitor slow queries

## Performance Tuning

1. **Database**: Configure PostgreSQL for your workload
2. **Connection Pooling**: Adjust SQLAlchemy pool settings
3. **Caching**: Implement Redis for frequently accessed data
4. **Async Operations**: Use background tasks for heavy operations

