#!/bin/bash
# Bash setup script for job-automation-service

echo "Setting up Job Automation Service..."

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "Error: Please run this script from the job-automation-service directory"
    exit 1
fi

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error installing dependencies"
    exit 1
fi

# Run migrations
echo ""
echo "Running database migrations..."
alembic upgrade head

if [ $? -ne 0 ]; then
    echo "Error running migrations"
    exit 1
fi

# Initialize skill profile
echo ""
echo "Initializing skill profile..."
python scripts/init_skill_profile.py

if [ $? -ne 0 ]; then
    echo "Error initializing skill profile"
    exit 1
fi

echo ""
echo "Setup complete! You can now start the service with:"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Or use Docker:"
echo "  docker-compose up -d"

