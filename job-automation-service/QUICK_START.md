# Quick Start Guide - Job Automation Service

## Prerequisites

1. **Python 3.8+** installed
2. **PostgreSQL** database running
3. **Dependencies** installed

## Setup Steps

### 1. Install Dependencies

```powershell
cd d:\software\job-automation-service
pip install -r requirements.txt
```

**Note**: If you're using a virtual environment, activate it first:
```powershell
# Create venv (if needed)
python -m venv venv

# Activate venv
.\venv\Scripts\Activate.ps1

# Then install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Make sure your `.env` file or environment variables are set with:
- Database connection string
- API keys (Adzuna, JSearch, etc.)

### 3. Start the Server

```powershell
cd d:\software\job-automation-service
.\restart_server.ps1
```

Or manually:
```powershell
cd d:\software\job-automation-service
$env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

### 4. Verify Installation

```powershell
cd d:\software\job-automation-service
python verify_jobs_saved.py
```

## Common Issues

### ModuleNotFoundError

**Error**: `ModuleNotFoundError: No module named 'httpx'`

**Solution**: Install dependencies:
```powershell
pip install -r requirements.txt
```

### Database Connection Error

**Error**: Cannot connect to database

**Solution**: 
1. Make sure PostgreSQL is running
2. Check database connection string in environment variables
3. Verify database exists and credentials are correct

### Port Already in Use

**Error**: Port 8004 is already in use

**Solution**: 
```powershell
# Stop existing process
.\restart_server.ps1
# This script will automatically stop any existing server
```

## Next Steps

After setup is complete, see `IMPLEMENTATION_COMPLETE.md` for:
- Testing job search functionality
- Backfilling legacy jobs
- Testing other job sources


