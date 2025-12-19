#!/bin/bash
# Update and patch management script
# Usage: ./update.sh [--type TYPE] [--service SERVICE] [--dry-run]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

UPDATE_TYPE="all"
SERVICE_NAME=""
DRY_RUN=false
BACKUP_BEFORE_UPDATE=true

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --type)
            UPDATE_TYPE="$2"
            shift 2
            ;;
        --service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --no-backup)
            BACKUP_BEFORE_UPDATE=false
            shift
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Update system packages
update_system() {
    log "Updating system packages..."
    
    if [ "$DRY_RUN" = true ]; then
        log "[DRY RUN] Would update system packages"
        return 0
    fi
    
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get upgrade -y
    elif command -v yum &> /dev/null; then
        yum update -y
    else
        error "Package manager not found"
    fi
    
    log "System packages updated"
}

# Update Docker images
update_docker_images() {
    log "Updating Docker images..."
    
    if [ "$DRY_RUN" = true ]; then
        log "[DRY RUN] Would pull latest Docker images"
        return 0
    fi
    
    cd "$PROJECT_ROOT"
    docker compose pull
    
    log "Docker images updated"
}

# Update application
update_application() {
    log "Updating application..."
    
    if [ "$DRY_RUN" = true ]; then
        log "[DRY RUN] Would update application code"
        return 0
    fi
    
    cd "$PROJECT_ROOT"
    
    # Pull latest code
    if [ -d ".git" ]; then
        git pull origin main || git pull origin master
    fi
    
    # Rebuild and restart services
    if [ -n "$SERVICE_NAME" ]; then
        docker compose build "$SERVICE_NAME"
        docker compose up -d "$SERVICE_NAME"
    else
        docker compose build
        docker compose up -d
    fi
    
    log "Application updated"
}

# Validate update
validate_update() {
    log "Validating update..."
    
    sleep 10
    
    # Run health checks
    if [ -f "$SCRIPT_DIR/health-check.sh" ]; then
        if [ -n "$SERVICE_NAME" ]; then
            "$SCRIPT_DIR/health-check.sh" --service "$SERVICE_NAME" || {
                error "Health check failed after update"
            }
        else
            "$SCRIPT_DIR/health-check.sh" || {
                error "Health check failed after update"
            }
        fi
    fi
    
    log "Update validated successfully"
}

# Rollback on failure
rollback_update() {
    log "Update failed, rolling back..."
    
    if [ -f "$SCRIPT_DIR/rollback.sh" ]; then
        "$SCRIPT_DIR/rollback.sh" --latest || {
            error "Rollback failed"
        }
    else
        error "Rollback script not found"
    fi
}

# Main update process
main() {
    log "Starting update process (type: $UPDATE_TYPE)"
    
    # Backup before update
    if [ "$BACKUP_BEFORE_UPDATE" = true ] && [ "$DRY_RUN" = false ]; then
        log "Creating backup before update..."
        if [ -f "$SCRIPT_DIR/backup.sh" ]; then
            "$SCRIPT_DIR/backup.sh" --quick || warning "Backup failed, continuing anyway..."
        fi
    fi
    
    # Perform updates based on type
    case $UPDATE_TYPE in
        system)
            update_system
            ;;
        docker)
            update_docker_images
            ;;
        application)
            update_application
            ;;
        all)
            update_system
            update_docker_images
            update_application
            ;;
        *)
            error "Unknown update type: $UPDATE_TYPE"
            ;;
    esac
    
    # Validate update
    if [ "$DRY_RUN" = false ]; then
        if ! validate_update; then
            rollback_update
            error "Update validation failed, rolled back"
        fi
    fi
    
    log "Update process completed successfully"
}

main "$@"
