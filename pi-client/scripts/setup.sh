#!/bin/bash
# Setup script for Pi Client

set -e

echo "Pi Client Setup"
echo "================"

# Check if config exists
CONFIG_FILE="/etc/pi-client/config.yaml"
if [ -f "$CONFIG_FILE" ]; then
    read -p "Configuration file exists. Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
fi

# Get device information
echo ""
echo "Device Information:"
read -p "Device ID: " DEVICE_ID
read -p "Device Name: " DEVICE_NAME
read -p "Organization ID: " ORG_ID

# Get API information
echo ""
echo "API Configuration:"
read -p "API Base URL: " API_URL
read -p "Auth Token: " AUTH_TOKEN

# Get cache configuration
echo ""
echo "Cache Configuration:"
read -p "Cache Directory [~/.pi-client/cache]: " CACHE_DIR
CACHE_DIR=${CACHE_DIR:-~/.pi-client/cache}
read -p "Max Cache Size (MB) [5000]: " CACHE_SIZE
CACHE_SIZE=${CACHE_SIZE:-5000}

# Get display configuration
echo ""
echo "Display Configuration:"
read -p "Display Port [8080]: " DISPLAY_PORT
DISPLAY_PORT=${DISPLAY_PORT:-8080}
read -p "Display Mode (kiosk/interactive/presentation/dashboard) [kiosk]: " DISPLAY_MODE
DISPLAY_MODE=${DISPLAY_MODE:-kiosk}
read -p "Rotation (landscape/portrait) [landscape]: " ROTATION
ROTATION=${ROTATION:-landscape}

# Get hardware configuration
echo ""
echo "Hardware Configuration:"
read -p "Enable GPIO? (y/N): " -n 1 -r
GPIO_ENABLED=$([[ $REPLY =~ ^[Yy]$ ]] && echo "true" || echo "false")
echo
read -p "Enable Camera? (y/N): " -n 1 -r
CAMERA_ENABLED=$([[ $REPLY =~ ^[Yy]$ ]] && echo "true" || echo "false")
echo
read -p "Enable Audio? (Y/n): " -n 1 -r
AUDIO_ENABLED=$([[ ! $REPLY =~ ^[Nn]$ ]] && echo "true" || echo "false")
echo

# Create config file
echo ""
echo "Creating configuration file..."
sudo tee "$CONFIG_FILE" > /dev/null <<EOF
device:
  device_id: "$DEVICE_ID"
  device_name: "$DEVICE_NAME"
  organization_id: $ORG_ID

api:
  base_url: "$API_URL"
  auth_token: "$AUTH_TOKEN"

cache:
  directory: "$CACHE_DIR"
  max_size_mb: $CACHE_SIZE
  ttl_hours: 168

display:
  port: $DISPLAY_PORT
  rotation: "$ROTATION"
  fullscreen: true
  mode: "$DISPLAY_MODE"

hardware:
  gpio_enabled: $GPIO_ENABLED
  camera_enabled: $CAMERA_ENABLED
  audio_enabled: $AUDIO_ENABLED

security:
  cert_path: "/etc/pi-client/certs/device.pem"
  encryption_enabled: true

sync_interval: 3600
EOF

sudo chmod 600 "$CONFIG_FILE"
sudo chown pi-client:pi-client "$CONFIG_FILE"

echo "Configuration saved to $CONFIG_FILE"

# Register device
echo ""
read -p "Register device with server now? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "Registering device..."
    # This would call the registration API
    echo "Device registration would happen here"
fi

echo ""
echo "Setup complete!"
echo "Start the service with: sudo systemctl start pi-client"




