#!/bin/bash
# Deployment script for Pi Client

set -e

REMOTE_HOST="${1:-}"
REMOTE_USER="${2:-pi}"
REMOTE_DIR="${3:-/opt/pi-client}"

if [ -z "$REMOTE_HOST" ]; then
    echo "Usage: $0 <remote_host> [remote_user] [remote_dir]"
    echo "Example: $0 192.168.1.100 pi /opt/pi-client"
    exit 1
fi

echo "Deploying Pi Client to $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR"

# Create remote directory
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR"

# Copy files
echo "Copying files..."
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='venv' --exclude='.venv' \
    ./ "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

# Install on remote
echo "Installing on remote host..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && sudo ./scripts/install.sh"

# Restart service
echo "Restarting service..."
ssh "$REMOTE_USER@$REMOTE_HOST" "sudo systemctl restart pi-client"

echo "Deployment complete!"
