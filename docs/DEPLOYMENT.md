# Production Deployment Guide

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- 20GB+ free disk space
- Domain name (optional, for HTTPS)
- SSL/TLS certificates (for HTTPS)

## Pre-Deployment Checklist

### 1. Security Configuration

**Critical: Set required secrets before deployment - application will NOT start without them!**

- [ ] **REQUIRED**: Generate and set `SECRET_KEY` (must be at least 32 characters)
- [ ] **REQUIRED**: Generate and set `JWT_SECRET_KEY` (must be at least 32 characters)
- [ ] Change all service default passwords
- [ ] Configure proper CORS origins
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Review and update `.env` file

**⚠️ WARNING**: The application will fail to start if `SECRET_KEY` or `JWT_SECRET_KEY` are missing or shorter than 32 characters. These are mandatory with no default values.

### 2. Environment Variables

Create a `.env` file from `.env.example` and configure:

```bash
# Application Secrets (REQUIRED - Must be set, no defaults!)
# ⚠️ Application will NOT start without these variables set
# Both must be at least 32 characters long
SECRET_KEY=your-very-long-random-secret-key-here  # Minimum 32 characters
JWT_SECRET_KEY=your-jwt-secret-key-here  # Minimum 32 characters

# Database
DATABASE_URL=postgresql://platform:strong-password@postgres:5432/platform

# Service URLs (update if using different ports/hosts)
SEAFILE_URL=http://seafile:8000
JELLYFIN_URL=http://jellyfin:8096
GITEA_URL=http://gitea:3000
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
VAULTWARDEN_URL=http://vaultwarden:80

# Service API Tokens (configure after service setup)
SEAFILE_API_TOKEN=your-seafile-token
JELLYFIN_API_KEY=your-jellyfin-key
GITEA_API_TOKEN=your-gitea-token
VAULTWARDEN_ADMIN_TOKEN=your-vaultwarden-token
BOOKSTACK_APP_KEY=your-bookstack-key
BOOKSTACK_DB_PASSWORD=strong-database-password

# CORS Configuration (restrict for production)
CORS_ORIGINS=["https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true

# Debug Mode (MUST be False in production)
DEBUG=False
```

### 3. Generate Secure Secrets

**MANDATORY**: You must generate and set `SECRET_KEY` and `JWT_SECRET_KEY` before starting the application. Use these commands:

```bash
# Generate SECRET_KEY (REQUIRED - copy output to .env file)
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY (REQUIRED - copy output to .env file)
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate database password (optional, for database security)
openssl rand -base64 32
```

**Important Notes:**
- Both `SECRET_KEY` and `JWT_SECRET_KEY` are **required** - the application will not start without them
- Each secret must be at least 32 characters long (the commands above generate 43-character secrets)
- Store these secrets securely and never commit them to version control
- Use different values for `SECRET_KEY` and `JWT_SECRET_KEY` (do not reuse the same value)

## Deployment Steps

### Step 1: Clone and Prepare

```bash
git clone <repository-url>
cd software
cp .env.example .env
# Edit .env with your configuration
```

### Step 2: Configure Docker Compose

Review `docker-compose.yml` and update:
- Port mappings if needed
- Volume paths for data persistence
- Resource limits
- Network configuration

### Step 3: Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f platform
```

### Step 4: Initialize Database

```bash
# Access platform container
docker exec -it platform-api bash

# Initialize database (only needed once)
curl -X POST http://localhost:8000/api/auth/init-db

# Exit container
exit
```

### Step 5: Create Admin User

```bash
# Register admin user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@yourdomain.com",
    "password": "your-secure-password"
  }'

# Make user admin (connect to database)
docker exec -it platform-postgres psql -U platform -d platform
```

In PostgreSQL:
```sql
UPDATE users SET is_admin = true WHERE username = 'admin';
\q
```

### Step 6: Register Services

Use the API or admin interface to register services:

```bash
# Get admin token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/token \
  -d "username=admin&password=your-secure-password" \
  | jq -r '.access_token')

# Register Seafile
curl -X POST http://localhost:8000/api/services \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "seafile",
    "service_type": "file_storage",
    "base_url": "http://seafile:8000",
    "api_url": "http://seafile:8000/api2",
    "health_check_url": "http://seafile:8000/api2/ping/",
    "requires_auth": true,
    "auth_token": "your-seafile-token"
  }'

# Repeat for other services...
```

## HTTPS Configuration

### Option 1: Nginx with Let's Encrypt

1. Install Certbot:
```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

2. Configure Nginx for your domain:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. Obtain SSL certificate:
```bash
sudo certbot --nginx -d yourdomain.com
```

### Option 2: Reverse Proxy with Traefik

Update `docker-compose.yml` to use Traefik with automatic HTTPS.

### Option 3: Cloudflare Proxy

Use Cloudflare as a reverse proxy with SSL termination.

## Backup Strategy

### Database Backup

```bash
# Create backup
docker exec platform-postgres pg_dump -U platform platform > backup_$(date +%Y%m%d).sql

# Restore backup
docker exec -i platform-postgres psql -U platform platform < backup_20240101.sql
```

### Automated Backups

Create a cron job:
```bash
0 2 * * * docker exec platform-postgres pg_dump -U platform platform | gzip > /backups/platform_$(date +\%Y\%m\%d).sql.gz
```

### Service Data Backups

Backup Docker volumes:
```bash
docker run --rm -v platform_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Monitoring and Maintenance

### Health Checks

```bash
# Check all services
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/health/services

# Check specific service
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/health/services/1
```

### Log Management

```bash
# View platform logs
docker-compose logs -f platform

# View all logs
docker-compose logs -f

# Rotate logs (configure logrotate)
```

### Updates

```bash
# Pull latest images
docker-compose pull

# Restart services
docker-compose up -d

# Check for updates
docker-compose ps
```

## Performance Tuning

### Database Optimization

1. Configure PostgreSQL:
```sql
-- In postgresql.conf
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
```

2. Create indexes:
```sql
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_services_type ON services(service_type);
```

### Application Optimization

1. Enable connection pooling
2. Configure async workers:
```bash
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

3. Add caching layer (Redis)

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose logs <service-name>

# Check resource usage
docker stats

# Restart service
docker-compose restart <service-name>
```

### Database Connection Issues

```bash
# Test connection
docker exec -it platform-postgres psql -U platform -d platform

# Check database status
docker-compose ps postgres
```

### Port Conflicts

```bash
# Check port usage
netstat -tulpn | grep :8000

# Update docker-compose.yml port mappings
```

## Security Hardening

1. **Firewall Configuration**
   - Only expose necessary ports (80, 443)
   - Block direct access to service ports
   - Use fail2ban for brute force protection

2. **Regular Updates**
   - Update Docker images regularly
   - Update system packages
   - Monitor security advisories

3. **Access Control**
   - Use strong passwords
   - Enable 2FA where possible
   - Regular security audits
   - Monitor access logs

4. **Network Security**
   - Use private Docker networks
   - Implement network segmentation
   - Use VPN for remote access

## Disaster Recovery

### Recovery Plan

1. **Database Recovery**
   ```bash
   # Restore from backup
   docker exec -i platform-postgres psql -U platform platform < backup.sql
   ```

2. **Service Recovery**
   ```bash
   # Recreate services
   docker-compose down
   docker-compose up -d
   ```

3. **Full System Recovery**
   - Restore database backup
   - Restore service data volumes
   - Update configuration
   - Restart all services

## Scaling

### Horizontal Scaling

1. Run multiple API instances:
```yaml
platform:
  deploy:
    replicas: 3
```

2. Use load balancer (Nginx/Traefik)

3. Configure database connection pooling

### Vertical Scaling

1. Increase container resources
2. Optimize database queries
3. Add caching layer

## Deployment Playbooks

### Playbook 1: Initial Deployment

**Objective**: Deploy platform from scratch on a new server

**Steps**:

1. **Server Preparation**
   ```bash
   # Update system
   sudo apt-get update && sudo apt-get upgrade -y
   
   # Install Docker and Docker Compose
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo apt-get install docker-compose-plugin -y
   
   # Add user to docker group
   sudo usermod -aG docker $USER
   ```

2. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd software
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with secure values
   nano .env
   ```

4. **Generate Secrets**
   ```bash
   # Generate SECRET_KEY
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Generate JWT_SECRET_KEY
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Generate database password
   openssl rand -base64 32
   ```

5. **Start Services**
   ```bash
   docker-compose up -d
   ```

6. **Initialize Database**
   ```bash
   # Wait for services to be ready
   sleep 10
   
   # Initialize database
   curl -X POST http://localhost:8000/api/auth/init-db
   ```

7. **Create Admin User**
   ```bash
   # Register user
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "username": "admin",
       "email": "admin@example.com",
       "password": "secure-password"
     }'
   
   # Make user admin
   docker exec -it platform-postgres psql -U platform -d platform
   # In PostgreSQL:
   UPDATE users SET is_admin = true WHERE username = 'admin';
   \q
   ```

8. **Register Services**
   ```bash
   # Get admin token
   TOKEN=$(curl -X POST http://localhost:8000/api/auth/token \
     -d "username=admin&password=secure-password" \
     | jq -r '.access_token')
   
   # Register services (see Service Registration Procedures below)
   ```

9. **Verify Deployment**
   ```bash
   # Check health
   curl http://localhost:8000/api/health
   
   # Check services
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/health/services
   ```

### Playbook 2: Production Deployment

**Objective**: Deploy platform in production with HTTPS

**Prerequisites**: Domain name, server with public IP

**Steps**:

1. **Follow Initial Deployment steps 1-7**

2. **Configure Domain DNS**
   - Point domain A record to server IP
   - Wait for DNS propagation

3. **Obtain SSL Certificate**
   ```bash
   # Install Certbot
   sudo apt-get install certbot python3-certbot-nginx -y
   
   # Stop Nginx container temporarily
   docker-compose stop nginx
   
   # Obtain certificate
   sudo certbot certonly --standalone -d yourdomain.com
   ```

4. **Configure Nginx for HTTPS**
   ```nginx
   # Update nginx/nginx.conf with SSL configuration
   server {
       listen 443 ssl http2;
       server_name yourdomain.com;
       
       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
       
       # SSL configuration
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;
       ssl_prefer_server_ciphers on;
       
       # Security headers
       add_header Strict-Transport-Security "max-age=31536000" always;
       add_header X-Frame-Options "DENY" always;
       add_header X-Content-Type-Options "nosniff" always;
       
       # Proxy configuration (same as HTTP)
       location / {
           proxy_pass http://platform:8000;
           # ... rest of proxy config
       }
   }
   
   # HTTP to HTTPS redirect
   server {
       listen 80;
       server_name yourdomain.com;
       return 301 https://$server_name$request_uri;
   }
   ```

5. **Mount SSL Certificates**
   ```yaml
   # Update docker-compose.yml
   nginx:
     volumes:
       - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
       - /etc/letsencrypt:/etc/letsencrypt:ro
   ```

6. **Restart Services**
   ```bash
   docker-compose restart nginx
   ```

7. **Configure Firewall**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

8. **Set Up Auto-Renewal**
   ```bash
   # Add to crontab
   sudo crontab -e
   # Add:
   0 3 * * * certbot renew --quiet && docker-compose restart nginx
   ```

### Playbook 3: Update Deployment

**Objective**: Update platform to new version

**Steps**:

1. **Backup Current State**
   ```bash
   # Backup database
   ./scripts/backup.sh
   
   # Backup volumes
   docker run --rm -v platform_postgres_data:/data \
     -v $(pwd)/backups:/backup alpine \
     tar czf /backup/volumes_$(date +%Y%m%d).tar.gz /data
   ```

2. **Pull Latest Code**
   ```bash
   git pull origin main
   ```

3. **Update Environment**
   ```bash
   # Review .env.example for new variables
   # Update .env if needed
   ```

4. **Pull Latest Images**
   ```bash
   docker-compose pull
   ```

5. **Update Services**
   ```bash
   # Stop services
   docker-compose down
   
   # Start with new images
   docker-compose up -d
   ```

6. **Run Migrations** (if applicable)
   ```bash
   docker exec -it platform-api alembic upgrade head
   ```

7. **Verify Update**
   ```bash
   # Check health
   curl http://localhost:8000/api/health
   
   # Check service versions
   docker-compose ps
   ```

## Service Registration Procedures

### Procedure 1: Register Seafile

```bash
# Get admin token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/token \
  -d "username=admin&password=password" | jq -r '.access_token')

# Get Seafile API token (from Seafile admin panel)
SEAFILE_TOKEN="your-seafile-api-token"

# Register service
curl -X POST http://localhost:8000/api/services \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"seafile\",
    \"service_type\": \"file_storage\",
    \"base_url\": \"http://seafile:80\",
    \"api_url\": \"http://seafile:80/api2\",
    \"health_check_url\": \"http://seafile:80/api2/ping/\",
    \"requires_auth\": true,
    \"auth_token\": \"$SEAFILE_TOKEN\"
  }"
```

### Procedure 2: Register Jellyfin

```bash
# Get Jellyfin API key (from Jellyfin admin panel)
JELLYFIN_KEY="your-jellyfin-api-key"

# Register service
curl -X POST http://localhost:8000/api/services \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"jellyfin\",
    \"service_type\": \"media_server\",
    \"base_url\": \"http://jellyfin:8096\",
    \"api_url\": \"http://jellyfin:8096\",
    \"health_check_url\": \"http://jellyfin:8096/System/Ping\",
    \"requires_auth\": true,
    \"auth_token\": \"$JELLYFIN_KEY\"
  }"
```

### Procedure 3: Register Gitea

```bash
# Get Gitea API token (from Gitea settings)
GITEA_TOKEN="your-gitea-token"

# Register service
curl -X POST http://localhost:8000/api/services \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"gitea\",
    \"service_type\": \"dev_tools\",
    \"base_url\": \"http://gitea:3000\",
    \"api_url\": \"http://gitea:3000/api/v1\",
    \"health_check_url\": \"http://gitea:3000/api/v1/version\",
    \"requires_auth\": true,
    \"auth_token\": \"$GITEA_TOKEN\"
  }"
```

### Procedure 4: Register Prometheus

```bash
# Register service (no auth required)
curl -X POST http://localhost:8000/api/services \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"prometheus\",
    \"service_type\": \"monitoring\",
    \"base_url\": \"http://prometheus:9090\",
    \"api_url\": \"http://prometheus:9090/api/v1\",
    \"health_check_url\": \"http://prometheus:9090/-/healthy\",
    \"requires_auth\": false
  }"
```

### Procedure 5: Register Grafana

```bash
# Register service
curl -X POST http://localhost:8000/api/services \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"grafana\",
    \"service_type\": \"monitoring\",
    \"base_url\": \"http://grafana:3000\",
    \"api_url\": \"http://grafana:3000/api\",
    \"health_check_url\": \"http://grafana:3000/api/health\",
    \"requires_auth\": true,
    \"auth_token\": \"admin:admin\"
  }"
```

### Procedure 6: Register Vaultwarden

```bash
# Get Vaultwarden admin token (from environment)
VAULTWARDEN_TOKEN="your-admin-token"

# Register service
curl -X POST http://localhost:8000/api/services \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"vaultwarden\",
    \"service_type\": \"security\",
    \"base_url\": \"http://vaultwarden:80\",
    \"api_url\": \"http://vaultwarden:80\",
    \"health_check_url\": \"http://vaultwarden:80/alive\",
    \"requires_auth\": true,
    \"auth_token\": \"$VAULTWARDEN_TOKEN\"
  }"
```

### Procedure 7: Register BookStack

```bash
# Register service
curl -X POST http://localhost:8000/api/services \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"bookstack\",
    \"service_type\": \"productivity\",
    \"base_url\": \"http://bookstack:80\",
    \"api_url\": \"http://bookstack:80/api\",
    \"health_check_url\": \"http://bookstack:80\",
    \"requires_auth\": false
  }"
```

## Backup and Recovery Procedures

### Automated Backup Script

Create `scripts/backup.sh`:

```bash
#!/bin/bash
# Backup script for platform

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/platform_backup_$DATE"

mkdir -p $BACKUP_PATH

# Backup database
echo "Backing up database..."
docker exec platform-postgres pg_dump -U platform platform | gzip > \
  $BACKUP_PATH/database.sql.gz

# Backup volumes
echo "Backing up volumes..."
docker run --rm \
  -v platform_postgres_data:/data \
  -v $BACKUP_PATH:/backup \
  alpine tar czf /backup/postgres_data.tar.gz /data

# Backup configuration
echo "Backing up configuration..."
cp .env $BACKUP_PATH/
cp docker-compose.yml $BACKUP_PATH/

# Create archive
cd $BACKUP_DIR
tar czf platform_backup_$DATE.tar.gz platform_backup_$DATE/
rm -rf platform_backup_$DATE

echo "Backup completed: $BACKUP_DIR/platform_backup_$DATE.tar.gz"

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "platform_backup_*.tar.gz" -mtime +7 -delete
```

Make executable:
```bash
chmod +x scripts/backup.sh
```

### Recovery Procedure

#### Database Recovery

```bash
# Stop services
docker-compose stop platform

# Restore database
gunzip < backup_20240101.sql.gz | \
  docker exec -i platform-postgres psql -U platform -d platform

# Restart services
docker-compose start platform
```

#### Full System Recovery

```bash
# 1. Extract backup
tar xzf platform_backup_20240101.tar.gz
cd platform_backup_20240101

# 2. Restore volumes
docker run --rm \
  -v platform_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_data.tar.gz -C /

# 3. Restore database
gunzip < database.sql.gz | \
  docker exec -i platform-postgres psql -U platform -d platform

# 4. Restore configuration
cp .env ../.env
cp docker-compose.yml ../docker-compose.yml

# 5. Restart services
cd ..
docker-compose up -d
```

## Enhanced Troubleshooting Guide

### Issue: Services Not Starting

**Symptoms**: Containers exit immediately or fail to start

**Diagnosis**:
```bash
# Check container logs
docker-compose logs <service-name>

# Check container status
docker-compose ps

# Check resource usage
docker stats

# Check Docker daemon
sudo systemctl status docker
```

**Solutions**:
1. **Port conflicts**: Change port mappings in `docker-compose.yml`
2. **Insufficient resources**: Increase Docker memory/CPU limits
3. **Volume permissions**: Fix volume mount permissions
4. **Configuration errors**: Check `.env` file for syntax errors

### Issue: Database Connection Errors

**Symptoms**: "Connection refused" or "Authentication failed"

**Diagnosis**:
```bash
# Test database connection
docker exec -it platform-postgres psql -U platform -d platform

# Check database logs
docker-compose logs postgres

# Verify connection string
docker exec platform-api env | grep DATABASE_URL
```

**Solutions**:
1. **Wrong credentials**: Update `DATABASE_URL` in `.env`
2. **Database not ready**: Wait for database to be healthy
3. **Network issues**: Verify containers are on same network
4. **Database full**: Check disk space: `df -h`

### Issue: Authentication Failures

**Symptoms**: "Could not validate credentials" errors

**Diagnosis**:
```bash
# Check JWT secret key
docker exec platform-api env | grep JWT_SECRET_KEY

# Test token generation
curl -X POST http://localhost:8000/api/auth/token \
  -d "username=admin&password=password"

# Check user in database
docker exec -it platform-postgres psql -U platform -d platform
SELECT username, is_active FROM users;
```

**Solutions**:
1. **Invalid credentials**: Verify username/password
2. **User inactive**: Activate user: `UPDATE users SET is_active=true WHERE username='user';`
3. **Token expired**: Request new token
4. **JWT secret changed**: Restart all services after changing JWT_SECRET_KEY

### Issue: Service Health Checks Failing

**Symptoms**: Services show as "unhealthy" in health checks

**Diagnosis**:
```bash
# Check service health directly
curl http://seafile:80/api2/ping/

# Check service logs
docker-compose logs seafile

# Test from platform container
docker exec platform-api curl http://seafile:80/api2/ping/
```

**Solutions**:
1. **Service not running**: Start service: `docker-compose start seafile`
2. **Wrong health check URL**: Update `health_check_url` in service registry
3. **Network connectivity**: Verify services are on same Docker network
4. **Service misconfiguration**: Check service-specific configuration

### Issue: Gateway Endpoints Returning 404

**Symptoms**: Gateway endpoints return "Service not found"

**Diagnosis**:
```bash
# List registered services
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/services

# Check service registration
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/services/1
```

**Solutions**:
1. **Service not registered**: Register service using procedures above
2. **Wrong service_type**: Verify service_type matches gateway route
3. **Service inactive**: Activate service: `UPDATE services SET is_active=true WHERE id=1;`

### Issue: High Memory Usage

**Symptoms**: System running out of memory

**Diagnosis**:
```bash
# Check container memory usage
docker stats

# Check system memory
free -h

# Check for memory leaks
docker-compose logs platform | grep -i memory
```

**Solutions**:
1. **Limit container memory**: Add memory limits in `docker-compose.yml`
2. **Restart services**: `docker-compose restart`
3. **Reduce service count**: Disable unused services
4. **Increase system memory**: Upgrade server RAM

### Issue: Slow Response Times

**Symptoms**: API responses are slow

**Diagnosis**:
```bash
# Check response times
time curl http://localhost:8000/api/health

# Check database performance
docker exec -it platform-postgres psql -U platform -d platform
EXPLAIN ANALYZE SELECT * FROM services;

# Check service response times
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/health/services
```

**Solutions**:
1. **Database optimization**: Add indexes, optimize queries
2. **Connection pooling**: Configure SQLAlchemy connection pool
3. **Service timeouts**: Increase timeout values for slow services
4. **Resource constraints**: Increase CPU/memory limits

## Support and Maintenance

### Daily Tasks
- Monitor health checks: `curl http://localhost:8000/api/health`
- Review error logs: `docker-compose logs --tail=100 platform`
- Check disk space: `df -h`

### Weekly Tasks
- Review all service logs
- Check backup completion
- Verify service health status
- Review security logs

### Monthly Tasks
- Update Docker images: `docker-compose pull && docker-compose up -d`
- Review and rotate secrets
- Security audit
- Performance review

### Quarterly Tasks
- Full system backup verification
- Disaster recovery drill
- Capacity planning review
- Documentation update
