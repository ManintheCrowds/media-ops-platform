#!/bin/bash
# Security patch management script
# Usage: ./patch-management.sh [--apply] [--test] [--schedule]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PATCH_ACTION="check"
APPLY_PATCHES=false
TEST_PATCHES=false
SCHEDULE_PATCHES=false

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --apply)
            APPLY_PATCHES=true
            PATCH_ACTION="apply"
            shift
            ;;
        --test)
            TEST_PATCHES=true
            shift
            ;;
        --schedule)
            SCHEDULE_PATCHES=true
            shift
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Check for available security patches
check_patches() {
    log "Checking for available security patches..."
    
    local updates_available=0
    
    if command -v apt-get &> /dev/null; then
        apt-get update -qq
        updates_available=$(apt-get upgrade -s | grep -c "^Inst" || true)
    elif command -v yum &> /dev/null; then
        updates_available=$(yum check-update --security -q 2>/dev/null | grep -c "^" || true)
    fi
    
    if [ "$updates_available" -gt 0 ]; then
        log "Found $updates_available security updates available"
        return 0
    else
        log "No security updates available"
        return 1
    fi
}

# Test patches in staging
test_patches() {
    log "Testing patches in staging environment..."
    
    # Run tests after applying patches
    if [ -f "$SCRIPT_DIR/../test_services.py" ]; then
        python3 "$SCRIPT_DIR/../test_services.py" || {
            error "Patch testing failed"
        }
    fi
    
    log "Patches tested successfully"
}

# Apply security patches
apply_patches() {
    log "Applying security patches..."
    
    # Backup before patching
    if [ -f "$SCRIPT_DIR/backup.sh" ]; then
        "$SCRIPT_DIR/backup.sh" --quick || warning "Backup failed"
    fi
    
    # Apply patches
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get upgrade -y --only-upgrade
        apt-get autoremove -y
    elif command -v yum &> /dev/null; then
        yum update --security -y
    fi
    
    # Update Docker images with security fixes
    cd "$PROJECT_ROOT"
    docker compose pull
    
    log "Security patches applied"
}

# Schedule patch application
schedule_patches() {
    log "Scheduling automatic patch application..."
    
    local cron_job="0 3 * * 0 $SCRIPT_DIR/patch-management.sh --apply >> $PROJECT_ROOT/logs/patch.log 2>&1"
    
    if crontab -l 2>/dev/null | grep -q "patch-management.sh"; then
        log "Patch schedule already exists"
    else
        (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
        log "Patch schedule added (Sundays at 3 AM)"
    fi
}

# Generate patch report
generate_report() {
    local report_file="$PROJECT_ROOT/logs/patch-report-$(date +%Y%m%d).txt"
    
    log "Generating patch report: $report_file"
    
    {
        echo "Security Patch Report - $(date)"
        echo "=================================="
        echo ""
        echo "System Information:"
        uname -a
        echo ""
        echo "Available Updates:"
        check_patches || echo "No updates available"
        echo ""
        echo "Docker Images:"
        docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}"
    } > "$report_file"
    
    log "Report generated: $report_file"
}

# Main patch management process
main() {
    case $PATCH_ACTION in
        check)
            check_patches
            generate_report
            ;;
        apply)
            if check_patches; then
                if [ "$TEST_PATCHES" = true ]; then
                    test_patches
                fi
                apply_patches
                log "Patches applied successfully"
            else
                log "No patches to apply"
            fi
            ;;
        schedule)
            schedule_patches
            ;;
        *)
            error "Unknown action: $PATCH_ACTION"
            ;;
    esac
}

main "$@"
