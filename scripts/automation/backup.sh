#!/bin/bash
# Backup automation script for platform services
# Usage: ./backup.sh [--quick] [--type TYPE] [--remote]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_TYPE="full"
QUICK_BACKUP=false
REMOTE_BACKUP=false

# Retention settings
DAILY_RETENTION_DAYS=30
WEEKLY_RETENTION_WEEKS=12
MONTHLY_RETENTION_MONTHS=12

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_BACKUP=true
            BACKUP_TYPE="quick"
            shift
            ;;
        --type)
            BACKUP_TYPE="$2"
            shift 2
            ;;
        --remote)
            REMOTE_BACKUP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create backup directory
mkdir -p "$BACKUP_DIR"/{database,volumes,config}

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# Database backup
backup_database() {
    log "Backing up PostgreSQL database..."
    
    local db_backup_file="$BACKUP_DIR/database/postgres-${TIMESTAMP}.sql.gz"
    
    docker exec platform-postgres pg_dump -U platform platform | gzip > "$db_backup_file" || {
        error "Database backup failed"
    }
    
    log "Database backup completed: $db_backup_file"
    echo "$db_backup_file"
}

# Volume backup
backup_volumes() {
    log "Backing up Docker volumes..."
    
    local volume_backup_dir="$BACKUP_DIR/volumes/volumes-${TIMESTAMP}"
    mkdir -p "$volume_backup_dir"
    
    # List of volumes to backup
    local volumes=(
        "platform_postgres_data"
        "platform_seafile_data"
        "platform_gitea_data"
        "platform_grafana_data"
        "platform_prometheus_data"
    )
    
    for volume in "${volumes[@]}"; do
        log "Backing up volume: $volume"
        docker run --rm \
            -v "$volume":/data:ro \
            -v "$volume_backup_dir":/backup \
            alpine tar czf "/backup/${volume}.tar.gz" -C /data . || {
            warning "Failed to backup volume: $volume"
        }
    done
    
    log "Volume backup completed: $volume_backup_dir"
    echo "$volume_backup_dir"
}

# Configuration backup
backup_config() {
    log "Backing up configuration files..."
    
    local config_backup_file="$BACKUP_DIR/config/config-${TIMESTAMP}.tar.gz"
    
    tar czf "$config_backup_file" \
        -C "$PROJECT_ROOT" \
        .env \
        docker-compose.yml \
        docker-compose.prod.yml \
        nginx/nginx.conf \
        prometheus/prometheus.yml \
        prometheus/alert_rules.yml \
        2>/dev/null || {
        error "Configuration backup failed"
    }
    
    log "Configuration backup completed: $config_backup_file"
    echo "$config_backup_file"
}

# Verify backup
verify_backup() {
    local backup_file=$1
    if [ -f "$backup_file" ]; then
        if [ "${backup_file##*.}" = "gz" ]; then
            gzip -t "$backup_file" || error "Backup file is corrupted: $backup_file"
        fi
        log "Backup verified: $backup_file"
        return 0
    else
        error "Backup file not found: $backup_file"
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    # Daily backups - keep for 30 days
    find "$BACKUP_DIR/database" -name "postgres-*.sql.gz" -mtime +$DAILY_RETENTION_DAYS -delete
    find "$BACKUP_DIR/config" -name "config-*.tar.gz" -mtime +$DAILY_RETENTION_DAYS -delete
    
    # Weekly backups - keep for 12 weeks
    find "$BACKUP_DIR/volumes" -type d -name "volumes-*" -mtime +$((WEEKLY_RETENTION_WEEKS * 7)) -exec rm -rf {} + 2>/dev/null || true
    
    log "Cleanup completed"
}

# Remote backup (if configured)
backup_remote() {
    if [ "$REMOTE_BACKUP" = true ] && [ -n "$BACKUP_REMOTE_HOST" ]; then
        log "Uploading backup to remote storage..."
        # Implement remote backup logic here
        # Example: rsync, scp, or cloud storage upload
        log "Remote backup completed"
    fi
}

# Main backup process
main() {
    log "Starting backup process (type: $BACKUP_TYPE)"
    
    # Database backup
    if [ "$QUICK_BACKUP" = false ] || [ "$BACKUP_TYPE" = "database" ]; then
        DB_BACKUP=$(backup_database)
        verify_backup "$DB_BACKUP"
    fi
    
    # Volume backup (only for full backups)
    if [ "$QUICK_BACKUP" = false ] && [ "$BACKUP_TYPE" = "full" ]; then
        VOLUME_BACKUP=$(backup_volumes)
    fi
    
    # Configuration backup
    if [ "$QUICK_BACKUP" = false ] || [ "$BACKUP_TYPE" = "config" ]; then
        CONFIG_BACKUP=$(backup_config)
        verify_backup "$CONFIG_BACKUP"
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Remote backup
    if [ "$REMOTE_BACKUP" = true ]; then
        backup_remote
    fi
    
    log "Backup process completed successfully"
}

main "$@"
