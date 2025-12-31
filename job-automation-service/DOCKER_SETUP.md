# Docker Setup Guide for Job Automation Service

## Prerequisites Check

✅ WSL 2 is installed and configured
✅ System is x64-based

## Step 1: Install Docker Desktop

### Option A: Download and Install Manually

1. **Download Docker Desktop for Windows:**
   - Visit: https://www.docker.com/products/docker-desktop/
   - Download the latest version (4.44.3 or newer for security)
   - Run the installer: `Docker Desktop Installer.exe`

2. **During Installation:**
   - Select "Use WSL 2 instead of Hyper-V" (recommended)
   - Complete the installation
   - Restart your computer if prompted

3. **After Installation:**
   - Launch Docker Desktop from Start menu
   - Wait for it to start (whale icon in system tray)
   - Verify installation:
     ```powershell
     docker --version
     docker-compose --version
     ```

### Option B: Install via Winget (if available)

```powershell
winget install Docker.DockerDesktop
```

After installation, restart your computer and launch Docker Desktop.

## Step 2: Start the Database

Once Docker is running:

```powershell
cd d:\software\job-automation-service
docker-compose up -d job-automation-db
```

This will:
- Download PostgreSQL 15 image
- Start the database container
- Expose database on `localhost:5433`

## Step 3: Verify Database is Running

```powershell
docker ps
```

You should see `job-automation-db` container running.

## Step 4: Run Database Migrations

```powershell
cd d:\software\job-automation-service

# Install Python dependencies first (if not already done)
pip install -r requirements.txt

# Set database URL for local connection
$env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"

# Run migrations
alembic upgrade head
```

## Step 5: Test the Setup

```powershell
# Run the script to fetch all jobs
python get_all_jobs.py
```

## Troubleshooting

### Docker Desktop won't start
- Ensure WSL 2 is running: `wsl --status`
- Check Windows features: Virtual Machine Platform and Windows Subsystem for Linux should be enabled
- Restart Docker Desktop

### Database connection errors
- Verify database is running: `docker ps`
- Check database logs: `docker logs job-automation-db`
- Ensure port 5433 is not in use

### Migration errors
- Ensure database container is healthy: `docker ps` shows "healthy"
- Check database logs: `docker logs job-automation-db`
- Try recreating the database:
  ```powershell
  docker-compose down -v
  docker-compose up -d job-automation-db
  ```











