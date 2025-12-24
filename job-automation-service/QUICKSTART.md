# Quick Start Guide

## Option 1: Using Docker (Recommended)

### Step 1: Start the database

```powershell
# From the root directory
docker-compose up -d job-automation-db

# Or from job-automation-service directory
docker-compose up -d job-automation-db
```

### Step 2: Run setup inside Docker

```powershell
# Start the service container
docker-compose up -d job-automation-service

# Run migrations
docker exec -it platform-job-automation alembic upgrade head

# Initialize skill profile
docker exec -it platform-job-automation python scripts/init_skill_profile.py
```

## Option 2: Local Development

### Step 1: Start PostgreSQL

You need PostgreSQL running locally. Options:

**Option A: Use Docker for database only**
```powershell
# From root directory
docker-compose up -d job-automation-db

# Database will be available on localhost:5433
```

**Option B: Install PostgreSQL locally**
- Download from https://www.postgresql.org/download/
- Default port: 5432

### Step 2: Create database and user

```powershell
# Connect to PostgreSQL
psql -U postgres

# Then run:
CREATE DATABASE jobautomation;
CREATE USER jobautomation WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE jobautomation TO jobautomation;
\q
```

### Step 3: Configure environment

Create `.env` file in `job-automation-service/`:

```env
# If using Docker database (exposed on port 5433)
DATABASE_URL=postgresql://jobautomation:password@localhost:5433/jobautomation

# If using local PostgreSQL (default port 5432)
# DATABASE_URL=postgresql://jobautomation:password@localhost:5432/jobautomation
```

### Step 4: Run setup script

```powershell
cd job-automation-service
.\setup.ps1
```

Or manually:

```powershell
cd job-automation-service

# Install dependencies
python -m pip install -r requirements.txt

# Set database URL for localhost
$env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5432/jobautomation"

# Run migrations
alembic upgrade head

# Initialize skill profile
python scripts/init_skill_profile.py
```

### Step 5: Start the service

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Troubleshooting

### "could not translate host name 'job-automation-db'"

This means you're running locally but trying to connect to Docker hostname.

**Solution:** Set `DATABASE_URL` environment variable:
```powershell
$env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5432/jobautomation"
```

### "No such container: platform-job-automation"

The Docker container isn't running. Start it:
```powershell
docker-compose up -d job-automation-service job-automation-db
```

### "could not connect to server"

PostgreSQL isn't running. Start it:
```powershell
# Using Docker
docker-compose up -d job-automation-db

# Or check local PostgreSQL service
```

### Database doesn't exist

Create it:
```powershell
psql -U postgres -c "CREATE DATABASE jobautomation;"
psql -U postgres -c "CREATE USER jobautomation WITH PASSWORD 'password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE jobautomation TO jobautomation;"
```

