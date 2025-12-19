#!/bin/bash

# Deployment script for Self-Hosted Platform

set -e

echo "🚀 Deploying Self-Hosted Platform..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please run setup.sh first."
    exit 1
fi

# Stop existing services
echo "🛑 Stopping existing services..."
docker-compose down

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose pull

# Build platform image
echo "🔨 Building platform image..."
docker-compose build platform

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Check service health
echo "🏥 Checking service health..."
docker-compose ps

echo "✅ Deployment complete!"
echo ""
echo "📊 View logs: docker-compose logs -f"
echo "🌐 Access dashboard: http://localhost/dashboard"


