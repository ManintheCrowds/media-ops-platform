#!/bin/bash
# Pi configuration synchronization script

set -e

DEVICE_ID="$1"
CONFIG_FILE="/etc/pi-client/config.yaml"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Backup current config
backup_config() {
    log "Backing up current configuration..."
    sudo cp "$CONFIG_FILE" "${CONFIG_FILE}.backup-$(date +%Y%m%d-%H%M%S)"
}

# Sync configuration
sync_config() {
    log "Synchronizing configuration for $DEVICE_ID..."
    
    # Use Ansible to sync config
    ansible-playbook -i "$DEVICE_ID," ansible/roles/pi-client/tasks/config.yml \
        -e "device_id=$DEVICE_ID"
}

# Detect changes
detect_changes() {
    if [ -f "${CONFIG_FILE}.backup" ]; then
        if ! diff -q "$CONFIG_FILE" "${CONFIG_FILE}.backup" > /dev/null; then
            log "Configuration changes detected"
            return 0
        fi
    fi
    return 1
}

main() {
    if [ -z "$DEVICE_ID" ]; then
        echo "Usage: $0 DEVICE_ID"
        exit 1
    fi
    
    backup_config
    if detect_changes || [ "$1" = "--force" ]; then
        sync_config
        log "Configuration synchronized"
    else
        log "No changes detected"
    fi
}

main "$@"
