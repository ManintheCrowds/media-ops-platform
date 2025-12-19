#!/bin/bash
# Individual service deployment script
# Usage: ./deploy-service.sh SERVICE_NAME

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SERVICE_NAME="$1"

if [ -z "$SERVICE_NAME" ]; then
    echo "Usage: $0 SERVICE_NAME"
    echo "Available services:"
    docker compose config --services 2>/dev/null || echo "Run from project root"
    exit 1
fi

# Service-specific health checks
check_service_health() {
    local service=$1
    case $service in
        platform)
            curl -f http://localhost:8000/api/health > /dev/null 2>&1
            ;;
        postgres)
            docker exec platform-postgres pg_isready -U platform > /dev/null 2>&1
            ;;
        prometheus)
            curl -f http://localhost:9090/-/healthy > /dev/null 2>&1
            ;;
        grafana)
            curl -f http://localhost:3001/api/health > /dev/null 2>&1
            ;;
        redis)
            docker exec platform-redis redis-cli ping > /dev/null 2>&1
            ;;
        *)
            # Generic health check - wait for container to be running
            sleep 10
            docker ps --filter "name=$service" --filter "status=running" | grep -q "$service"
            ;;
    esac
}

# Check dependencies
check_dependencies() {
    local service=$1
    case $service in
        platform)
            echo "Checking postgres dependency..."
            check_service_health postgres || {
                echo "ERROR: PostgreSQL is not healthy"
                exit 1
            }
            ;;
        seafile)
            echo "Checking seafile-db dependency..."
            check_service_health seafile-db || {
                echo "ERROR: Seafile database is not healthy"
                exit 1
            }
            ;;
        gitea)
            echo "Checking gitea-db dependency..."
            check_service_health gitea-db || {
                echo "ERROR: Gitea database is not healthy"
                exit 1
            }
            ;;
        bookstack)
            echo "Checking bookstack-db dependency..."
            check_service_health bookstack-db || {
                echo "ERROR: BookStack database is not healthy"
                exit 1
            }
            ;;
        education-service)
            echo "Checking education-db dependency..."
            check_service_health education-db || {
                echo "ERROR: Education database is not healthy"
                exit 1
            }
            ;;
    esac
}

echo "Deploying service: $SERVICE_NAME"

# Check if service exists
cd "$PROJECT_ROOT"
if ! docker compose config --services | grep -q "^${SERVICE_NAME}$"; then
    echo "ERROR: Service '$SERVICE_NAME' not found"
    exit 1
fi

# Check dependencies
check_dependencies "$SERVICE_NAME"

# Pull image if needed
echo "Pulling image for $SERVICE_NAME..."
docker compose pull "$SERVICE_NAME" || true

# Build if needed
if docker compose config | grep -A 5 "^\s*${SERVICE_NAME}:" | grep -q "build:"; then
    echo "Building $SERVICE_NAME..."
    docker compose build "$SERVICE_NAME"
fi

# Stop service
echo "Stopping $SERVICE_NAME..."
docker compose stop "$SERVICE_NAME" || true

# Remove old container
echo "Removing old container..."
docker compose rm -f "$SERVICE_NAME" || true

# Start service
echo "Starting $SERVICE_NAME..."
docker compose up -d "$SERVICE_NAME"

# Wait for service to be ready
echo "Waiting for $SERVICE_NAME to be ready..."
sleep 10

# Health check
echo "Checking health of $SERVICE_NAME..."
if check_service_health "$SERVICE_NAME"; then
    echo "✓ $SERVICE_NAME is healthy"
else
    echo "✗ $SERVICE_NAME health check failed"
    echo "Container logs:"
    docker compose logs --tail=50 "$SERVICE_NAME"
    exit 1
fi

echo "Service $SERVICE_NAME deployed successfully"
