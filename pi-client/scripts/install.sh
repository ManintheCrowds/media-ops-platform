#!/bin/bash
# Installation script for Pi Client

set -e

echo "Installing Pi Client..."

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "Warning: This script is designed for Raspberry Pi"
fi

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev

# Create pi-client user
if ! id "pi-client" &>/dev/null; then
    echo "Creating pi-client user..."
    sudo useradd -r -s /bin/false -d /var/lib/pi-client pi-client
fi

# Create directories
echo "Creating directories..."
sudo mkdir -p /etc/pi-client
sudo mkdir -p /var/lib/pi-client
sudo mkdir -p /var/log/pi-client
sudo mkdir -p /etc/pi-client/certs

# Set permissions
sudo chown -R pi-client:pi-client /var/lib/pi-client
sudo chown -R pi-client:pi-client /var/log/pi-client
sudo chmod 755 /etc/pi-client
sudo chmod 700 /etc/pi-client/certs

# Create virtual environment
echo "Creating Python virtual environment..."
sudo -u pi-client python3 -m venv /var/lib/pi-client/venv

# Install Python packages
echo "Installing Python packages..."
sudo -u pi-client /var/lib/pi-client/venv/bin/pip install --upgrade pip
sudo -u pi-client /var/lib/pi-client/venv/bin/pip install -r requirements.txt

# Install hardware packages if on Raspberry Pi
if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "Installing hardware packages..."
    sudo -u pi-client /var/lib/pi-client/venv/bin/pip install \
        RPi.GPIO \
        gpiozero \
        picamera2 \
        pygame
fi

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/pi-client.service > /dev/null <<EOF
[Unit]
Description=Pi Client for Educational Platform
After=network.target

[Service]
Type=simple
User=pi-client
Group=pi-client
WorkingDirectory=/var/lib/pi-client
Environment="PATH=/var/lib/pi-client/venv/bin"
ExecStart=/var/lib/pi-client/venv/bin/python -m pi_client.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

echo "Installation complete!"
echo "Next steps:"
echo "1. Run ./scripts/setup.sh to configure the client"
echo "2. Start the service: sudo systemctl start pi-client"
echo "3. Enable auto-start: sudo systemctl enable pi-client"


