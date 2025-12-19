#!/bin/bash
# Rollback script
# Usage: ./rollback.sh [--version VERSION] [--latest]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

VERSION=""
ROLLBACK_TO_LATEST=false

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
        --version)
            VERSION="$2"
            shift 2
            ;;
        --latest)
            ROLLBACK_TO_LATEST=true
            shift
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Get latest backup
get_latest_backup() {
    local backup_type=$1
    find "$PROJECT_ROOT/backups/$backup_type" -type f -name "*.gz" | sort -r | head -1
}

# Rollback database
rollback_database() {
    local backup_file=$(get_latest_backup database)
    
    if [ -z "$backup_file" ]; then
        error "No database backup found"
    fi
    
    log "Rolling back database from: $backup_file"
    
    # Stop services
    docker compose stop platform || true
    
    # Restore database
    gunzip -c "$backup_file" | docker exec -i platform-postgres psql -U platform platform
    
    # Start services
    docker compose start platform
    
    log "Database rollback completed"
}

# Rollback to git version
rollback_git() {
    if [ -n "$VERSION" ]; then
        log "Rolling back to version: $VERSION"
        git checkout "$VERSION"
    elif [ "$ROLLBACK_TO_LATEST" = true ]; then
        log "Rolling back to latest tag"
        git checkout $(git describe --tags --abbrev=0)
    else
        error "No version specified"
    fi
    
    # Rebuild and restart
    docker compose build
    docker compose up -d
}

# Verify rollback
verify_rollback() {
    log "Verifying rollback..."
    
    sleep 10
    
    if [ -f "$SCRIPT_DIR/health-check.sh" ]; then
        "$SCRIPT_DIR/health-check.sh" || {
            error "Rollback verification failed"
        }
    fi
    
    log "Rollback verified successfully"
}

# Main rollback process
main() {
    log "Starting rollback process"
    
    # Create backup before rollback
    if [ -f "$SCRIPT_DIR/backup.sh" ]; then
        "$SCRIPT_DIR/backup.sh" --quick
    fi
    
    # Rollback database
    rollback_database
    
    # Rollback code if version specified
    if [ -n "$VERSION" ] || [ "$ROLLBACK_TO_LATEST" = true ]; then
        rollback_git
    fi
    
    # Verify rollback
    verify_rollback
    
    log "Rollback completed successfully"
}

main "$@"
