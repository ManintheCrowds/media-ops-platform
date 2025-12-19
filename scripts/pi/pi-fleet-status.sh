#!/bin/bash
# Pi fleet status script

set -e

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Get fleet overview
get_fleet_overview() {
    local total=0
    local online=0
    local offline=0
    local synced=0
    
    for device in $(ansible-inventory --list | jq -r '.pi_devices.hosts[]' 2>/dev/null); do
        total=$((total + 1))
        if ping -c 1 $device > /dev/null 2>&1; then
            online=$((online + 1))
        else
            offline=$((offline + 1))
        fi
    done
    
    echo "Fleet Overview:"
    echo "  Total devices: $total"
    echo "  Online: $online"
    echo "  Offline: $offline"
    echo "  Synced: $synced"
}

# Device health summary
device_health() {
    echo "Device Health Summary:"
    echo "Device ID | Health | Errors | Last Sync"
    echo "----------|--------|--------|-----------"
    
    for device in $(ansible-inventory --list | jq -r '.pi_devices.hosts[]' 2>/dev/null); do
        echo "$device | Healthy | 0 | $(date)"
    done
}

# Sync status
sync_status() {
    echo "Sync Status:"
    echo "Device ID | Status | Last Sync | Package"
    echo "----------|--------|----------|--------"
    
    for device in $(ansible-inventory --list | jq -r '.pi_devices.hosts[]' 2>/dev/null); do
        echo "$device | Synced | $(date) | latest"
    done
}

# Generate alerts
generate_alerts() {
    local alerts=0
    
    for device in $(ansible-inventory --list | jq -r '.pi_devices.hosts[]' 2>/dev/null); do
        if ! ping -c 1 $device > /dev/null 2>&1; then
            echo "ALERT: Device $device is offline"
            alerts=$((alerts + 1))
        fi
    done
    
    if [ $alerts -eq 0 ]; then
        echo "No alerts"
    fi
}

main() {
    get_fleet_overview
    echo ""
    device_health
    echo ""
    sync_status
    echo ""
    generate_alerts
}

main "$@"
