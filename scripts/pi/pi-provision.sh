#!/bin/bash
# Raspberry Pi provisioning script
# Usage: ./pi-provision.sh DEVICE_ID DEVICE_NAME [OPTIONS]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

DEVICE_ID="$1"
DEVICE_NAME="$2"
API_URL="${API_URL:-http://localhost:8003}"
ORG_ID="${ORG_ID:-1}"

if [ -z "$DEVICE_ID" ] || [ -z "$DEVICE_NAME" ]; then
    echo "Usage: $0 DEVICE_ID DEVICE_NAME [API_URL] [ORG_ID]"
    exit 1
fi

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Check if running on Raspberry Pi
check_pi() {
    if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
        log "Warning: This script is designed for Raspberry Pi"
    fi
}

# Install prerequisites
install_prerequisites() {
    log "Installing prerequisites..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv git build-essential
}

# Install pi-client
install_pi_client() {
    log "Installing pi-client..."
    
    if [ -d "/opt/pi-client" ]; then
        log "pi-client already installed, updating..."
        cd /opt/pi-client
        git pull || true
    else
        sudo git clone https://github.com/your-org/pi-client.git /opt/pi-client
    fi
    
    sudo python3 -m venv /opt/pi-client/venv
    sudo /opt/pi-client/venv/bin/pip install -r /opt/pi-client/requirements.txt
}

# Generate certificates
generate_certificates() {
    log "Generating device certificates..."
    
    sudo mkdir -p /etc/pi-client/certs
    
    # Generate device certificate
    sudo openssl req -x509 -newkey rsa:4096 -keyout /etc/pi-client/certs/device-key.pem \
        -out /etc/pi-client/certs/device.pem -days 3650 -nodes \
        -subj "/CN=$DEVICE_ID"
    
    sudo chmod 600 /etc/pi-client/certs/device-key.pem
    sudo chmod 644 /etc/pi-client/certs/device.pem
}

# Configure pi-client
configure_pi_client() {
    log "Configuring pi-client..."
    
    sudo mkdir -p /etc/pi-client
    
    cat <<EOF | sudo tee /etc/pi-client/config.yaml
device:
  device_id: "$DEVICE_ID"
  device_name: "$DEVICE_NAME"

api:
  base_url: "$API_URL"
  timeout: 30

cache:
  directory: /var/lib/pi-client/cache
  max_size_mb: 5000
  ttl_hours: 168

display:
  port: 8080
  rotation: landscape
  fullscreen: true
  mode: kiosk

hardware:
  gpio_enabled: true
  camera_enabled: false
  audio_enabled: true

security:
  cert_path: /etc/pi-client/certs/device.pem
  key_path: /etc/pi-client/certs/device-key.pem
  encryption_enabled: true
EOF
}

# Register device
register_device() {
    log "Registering device with platform..."
    
    # Use Ansible or direct API call
    if command -v ansible-playbook &> /dev/null; then
        cd "$PROJECT_ROOT"
        ansible-playbook -i "$DEVICE_ID," ansible/playbooks/pi-provision.yml \
            -e "device_id=$DEVICE_ID" \
            -e "device_name=$DEVICE_NAME" \
            -e "pi_organization_id=$ORG_ID"
    else
        log "Ansible not available, skipping registration"
    fi
}

# Main provisioning
main() {
    log "Starting Pi provisioning for $DEVICE_ID ($DEVICE_NAME)"
    
    check_pi
    install_prerequisites
    install_pi_client
    generate_certificates
    configure_pi_client
    register_device
    
    log "Pi provisioning completed"
}

main "$@"
