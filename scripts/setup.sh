#!/bin/bash

# Setup script for Self-Hosted Platform

set -e

echo "🚀 Setting up Self-Hosted Platform..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and set your secrets before continuing!"
    read -p "Press Enter to continue after editing .env..."
fi

# Generate secrets if not set
if grep -q "change-me-in-production" .env; then
    echo "🔐 Generating secure secrets..."
    
    # Generate random secrets
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    
    # Update .env file (works on both Linux and macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        sed -i '' "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
    else
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
    fi
    
    echo "✅ Secrets generated and updated in .env"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p media
mkdir -p prometheus

# Pull Docker images
echo "📥 Pulling Docker images..."
docker-compose pull

# Start services
echo "🚀 Starting services..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Initialize database
echo "🗄️  Initializing database..."
docker-compose exec -T platform python -c "
from platform.models import Base
from platform.config import settings
from sqlalchemy import create_engine

engine = create_engine(settings.database_url)
Base.metadata.create_all(bind=engine)
print('Database initialized')
" || echo "⚠️  Database initialization may have failed. You can initialize it manually later."

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Create an admin user:"
echo "   curl -X POST http://localhost:8000/api/auth/register \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"username\":\"admin\",\"email\":\"admin@example.com\",\"password\":\"yourpassword\"}'"
echo ""
echo "2. Make user admin (connect to database):"
echo "   docker exec -it platform-postgres psql -U platform -d platform"
echo "   UPDATE users SET is_admin = true WHERE username = 'admin';"
echo ""
echo "3. Access the dashboard at: http://localhost/dashboard"
echo ""
echo "📊 View logs: docker-compose logs -f"
echo "🛑 Stop services: docker-compose down"


