#!/bin/bash
# Remote Pi update script
# Usage: ./pi-update.sh DEVICE_ID [--version VERSION] [--rollback]

set -e

DEVICE_ID="$1"
VERSION="latest"
ROLLBACK=false

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Update pi-client
update_pi_client() {
    log "Updating pi-client on $DEVICE_ID..."
    
    ssh pi@$DEVICE_ID <<EOF
        cd /opt/pi-client
        git pull
        /opt/pi-client/venv/bin/pip install -r requirements.txt --upgrade
        sudo systemctl restart pi-client
EOF
    
    log "Update completed"
}

# Verify update
verify_update() {
    log "Verifying update..."
    
    sleep 10
    
    # Check service status
    ssh pi@$DEVICE_ID "systemctl is-active pi-client" || {
        log "Service check failed, rolling back..."
        rollback_update
        exit 1
    }
    
    log "Update verified"
}

# Rollback update
rollback_update() {
    log "Rolling back update..."
    
    ssh pi@$DEVICE_ID <<EOF
        cd /opt/pi-client
        git checkout HEAD~1
        /opt/pi-client/venv/bin/pip install -r requirements.txt
        sudo systemctl restart pi-client
EOF
    
    log "Rollback completed"
}

main() {
    if [ -z "$DEVICE_ID" ]; then
        echo "Usage: $0 DEVICE_ID [--version VERSION] [--rollback]"
        exit 1
    fi
    
    if [ "$ROLLBACK" = true ]; then
        rollback_update
    else
        update_pi_client
        verify_update
    fi
}

main "$@"
