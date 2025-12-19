#!/bin/bash
# Backup scheduler script
# Sets up automated backup scheduling via cron

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"

# Backup schedules
DAILY_BACKUP_TIME="02:00"  # 2 AM daily
WEEKLY_BACKUP_DAY="0"      # Sunday
WEEKLY_BACKUP_TIME="01:00" # 1 AM

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Create cron job for daily backups
setup_daily_backup() {
    log "Setting up daily backup schedule..."
    
    local cron_job="0 2 * * * $BACKUP_SCRIPT --type database --type config >> $PROJECT_ROOT/logs/backup-daily.log 2>&1"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
        log "Daily backup cron job already exists"
    else
        (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
        log "Daily backup cron job added"
    fi
}

# Create cron job for weekly backups
setup_weekly_backup() {
    log "Setting up weekly backup schedule..."
    
    local cron_job="0 1 * * 0 $BACKUP_SCRIPT --type full >> $PROJECT_ROOT/logs/backup-weekly.log 2>&1"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "backup-weekly"; then
        log "Weekly backup cron job already exists"
    else
        (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
        log "Weekly backup cron job added"
    fi
}

# Remove cron jobs
remove_backup_schedule() {
    log "Removing backup schedules..."
    crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT" | crontab - || true
    log "Backup schedules removed"
}

# List current cron jobs
list_schedules() {
    log "Current backup schedules:"
    crontab -l 2>/dev/null | grep "$BACKUP_SCRIPT" || echo "No backup schedules found"
}

# Main
case "${1:-setup}" in
    setup)
        setup_daily_backup
        setup_weekly_backup
        log "Backup scheduling completed"
        list_schedules
        ;;
    remove)
        remove_backup_schedule
        ;;
    list)
        list_schedules
        ;;
    *)
        echo "Usage: $0 [setup|remove|list]"
        exit 1
        ;;
esac
