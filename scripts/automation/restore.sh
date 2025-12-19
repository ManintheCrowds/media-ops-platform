#!/bin/bash
# Backup restoration script
# Usage: ./restore.sh --type TYPE --file FILE

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"

RESTORE_TYPE=""
BACKUP_FILE=""
CONFIRM=false

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
            RESTORE_TYPE="$2"
            shift 2
            ;;
        --file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        --confirm)
            CONFIRM=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ -z "$RESTORE_TYPE" ] || [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 --type TYPE --file FILE [--confirm]"
    echo "Types: database, volumes, config"
    exit 1
fi

# List available backups
list_backups() {
    local type=$1
    case $type in
        database)
            find "$BACKUP_DIR/database" -name "postgres-*.sql.gz" -type f | sort -r
            ;;
        volumes)
            find "$BACKUP_DIR/volumes" -type d -name "volumes-*" | sort -r
            ;;
        config)
            find "$BACKUP_DIR/config" -name "config-*.tar.gz" -type f | sort -r
            ;;
    esac
}

# Restore database
restore_database() {
    local backup_file=$1
    
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
    fi
    
    log "Restoring database from: $backup_file"
    
    # Stop platform service
    log "Stopping platform service..."
    docker compose stop platform || true
    
    # Restore database
    log "Restoring database..."
    gunzip -c "$backup_file" | docker exec -i platform-postgres psql -U platform platform || {
        error "Database restoration failed"
    }
    
    # Start platform service
    log "Starting platform service..."
    docker compose start platform
    
    log "Database restoration completed"
}

# Restore volumes
restore_volumes() {
    local backup_dir=$1
    
    if [ ! -d "$backup_dir" ]; then
        error "Backup directory not found: $backup_dir"
    fi
    
    log "Restoring volumes from: $backup_dir"
    
    # Stop services
    log "Stopping services..."
    docker compose stop || true
    
    # Restore each volume
    for volume_backup in "$backup_dir"/*.tar.gz; do
        if [ -f "$volume_backup" ]; then
            volume_name=$(basename "$volume_backup" .tar.gz)
            log "Restoring volume: $volume_name"
            
            docker run --rm \
                -v "$volume_name":/data \
                -v "$backup_dir":/backup \
                alpine sh -c "rm -rf /data/* && tar xzf /backup/$(basename $volume_backup) -C /data" || {
                error "Failed to restore volume: $volume_name"
            }
        fi
    done
    
    # Start services
    log "Starting services..."
    docker compose start
    
    log "Volume restoration completed"
}

# Restore configuration
restore_config() {
    local backup_file=$1
    
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
    fi
    
    log "Restoring configuration from: $backup_file"
    
    # Extract to temporary directory
    local temp_dir=$(mktemp -d)
    tar xzf "$backup_file" -C "$temp_dir"
    
    # Restore files
    if [ -f "$temp_dir/.env" ]; then
        cp "$temp_dir/.env" "$PROJECT_ROOT/.env"
        log "Restored .env file"
    fi
    
    if [ -f "$temp_dir/docker-compose.yml" ]; then
        cp "$temp_dir/docker-compose.yml" "$PROJECT_ROOT/docker-compose.yml"
        log "Restored docker-compose.yml"
    fi
    
    # Restore other config files as needed
    
    rm -rf "$temp_dir"
    
    log "Configuration restoration completed"
}

# Main restore process
main() {
    if [ "$CONFIRM" = false ]; then
        echo "WARNING: This will restore from backup and may overwrite current data."
        echo "Backup file: $BACKUP_FILE"
        read -p "Are you sure you want to continue? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            log "Restore cancelled"
            exit 0
        fi
    fi
    
    case $RESTORE_TYPE in
        database)
            restore_database "$BACKUP_FILE"
            ;;
        volumes)
            restore_volumes "$BACKUP_FILE"
            ;;
        config)
            restore_config "$BACKUP_FILE"
            ;;
        *)
            error "Unknown restore type: $RESTORE_TYPE"
            ;;
    esac
    
    log "Restoration completed successfully"
}

main "$@"
