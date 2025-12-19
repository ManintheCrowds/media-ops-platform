#!/bin/bash
# Enhanced deployment script for platform services
# Usage: ./deploy.sh [--service SERVICE_NAME] [--no-backup] [--no-rollback]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
BACKUP_DIR="$PROJECT_ROOT/backups"
DEPLOY_LOG="$LOG_DIR/deploy-$(date +%Y%m%d-%H%M%S).log"

# Configuration
SERVICE_NAME=""
SKIP_BACKUP=false
SKIP_ROLLBACK=false
PRODUCTION=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$DEPLOY_LOG"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$DEPLOY_LOG"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$DEPLOY_LOG"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --no-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --no-rollback)
            SKIP_ROLLBACK=true
            shift
            ;;
        --production)
            PRODUCTION=true
            shift
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Create directories
mkdir -p "$LOG_DIR" "$BACKUP_DIR"

log "Starting deployment process..."

# Pre-deployment validation
log "Running pre-deployment validation..."

# Check Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    error "Docker is not installed"
fi

if ! docker compose version &> /dev/null; then
    error "Docker Compose is not available"
fi

# Check .env file
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    error ".env file not found. Please create it from .env.example"
fi

# Check disk space (at least 5GB free)
AVAILABLE_SPACE=$(df -BG "$PROJECT_ROOT" | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 5 ]; then
    error "Insufficient disk space. At least 5GB required, found ${AVAILABLE_SPACE}GB"
fi

# Backup before deployment
if [ "$SKIP_BACKUP" = false ]; then
    log "Creating backup before deployment..."
    if [ -f "$SCRIPT_DIR/backup.sh" ]; then
        "$SCRIPT_DIR/backup.sh" --quick || warning "Backup failed, continuing anyway..."
    else
        warning "Backup script not found, skipping backup"
    fi
fi

# Determine compose files
COMPOSE_FILES="-f $PROJECT_ROOT/docker-compose.yml"
if [ "$PRODUCTION" = true ] && [ -f "$PROJECT_ROOT/docker-compose.prod.yml" ]; then
    COMPOSE_FILES="$COMPOSE_FILES -f $PROJECT_ROOT/docker-compose.prod.yml"
fi

# Pull latest images
log "Pulling latest Docker images..."
cd "$PROJECT_ROOT"
docker compose $COMPOSE_FILES pull || error "Failed to pull images"

# Build platform image if needed
if [ -z "$SERVICE_NAME" ] || [ "$SERVICE_NAME" = "platform" ]; then
    log "Building platform image..."
    docker compose $COMPOSE_FILES build platform || error "Failed to build platform image"
fi

# Deploy services
if [ -n "$SERVICE_NAME" ]; then
    log "Deploying service: $SERVICE_NAME"
    docker compose $COMPOSE_FILES up -d "$SERVICE_NAME" || error "Failed to deploy $SERVICE_NAME"
else
    log "Deploying all services..."
    docker compose $COMPOSE_FILES up -d || error "Failed to deploy services"
fi

# Wait for services to be healthy
log "Waiting for services to be healthy..."
sleep 15

# Health check
log "Running health checks..."
if [ -f "$SCRIPT_DIR/health-check.sh" ]; then
    if [ -n "$SERVICE_NAME" ]; then
        "$SCRIPT_DIR/health-check.sh" --service "$SERVICE_NAME" || {
            error "Health check failed for $SERVICE_NAME"
        }
    else
        "$SCRIPT_DIR/health-check.sh" || {
            if [ "$SKIP_ROLLBACK" = false ]; then
                warning "Health check failed, attempting rollback..."
                if [ -f "$SCRIPT_DIR/rollback.sh" ]; then
                    "$SCRIPT_DIR/rollback.sh" --latest || error "Rollback failed"
                fi
            fi
            error "Health check failed"
        }
    fi
else
    warning "Health check script not found, skipping health verification"
fi

# Display service status
log "Deployment complete. Service status:"
docker compose $COMPOSE_FILES ps

log "Deployment successful!"
log "Log file: $DEPLOY_LOG"
