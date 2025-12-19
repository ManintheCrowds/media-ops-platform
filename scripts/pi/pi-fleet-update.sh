#!/bin/bash
# Fleet-wide Pi update script
# Usage: ./pi-fleet-update.sh [--batch-size SIZE] [--staged]

set -e

BATCH_SIZE=2
STAGED=true
DEVICE_LIST=""

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Get device list
get_devices() {
    # Get from inventory or API
    DEVICE_LIST=$(ansible-inventory --list | jq -r '.pi_devices.hosts[]' 2>/dev/null || echo "")
}

# Update batch
update_batch() {
    local devices=("$@")
    local failed_devices=()
    
    for device in "${devices[@]}"; do
        log "Updating device: $device"
        if "$SCRIPT_DIR/pi-update.sh" "$device"; then
            log "✓ $device updated successfully"
        else
            log "✗ $device update failed"
            failed_devices+=("$device")
        fi
    done
    
    if [ ${#failed_devices[@]} -gt 0 ]; then
        log "Failed devices: ${failed_devices[*]}"
        return 1
    fi
    return 0
}

# Staged rollout
staged_rollout() {
    log "Starting staged rollout (batch size: $BATCH_SIZE)"
    
    get_devices
    
    local devices_array=($DEVICE_LIST)
    local total=${#devices_array[@]}
    local current=0
    
    while [ $current -lt $total ]; do
        local batch=("${devices_array[@]:$current:$BATCH_SIZE}")
        log "Updating batch $((current/BATCH_SIZE + 1)): ${batch[*]}"
        
        if update_batch "${batch[@]}"; then
            log "Batch completed successfully, waiting before next batch..."
            sleep 60
        else
            log "Batch failed, stopping rollout"
            exit 1
        fi
        
        current=$((current + BATCH_SIZE))
    done
    
    log "Fleet update completed"
}

main() {
    if [ "$STAGED" = true ]; then
        staged_rollout
    else
        get_devices
        update_batch $DEVICE_LIST
    fi
}

main "$@"
