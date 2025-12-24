# PowerShell setup script for job-automation-service

Write-Host "Setting up Job Automation Service..." -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "app\main.py")) {
    Write-Host "Error: Please run this script from the job-automation-service directory" -ForegroundColor Red
    exit 1
}

# Check if Docker containers are running
$dockerRunning = docker ps --filter "name=job-automation-db" --format "{{.Names}}" | Select-String "job-automation-db"

if ($dockerRunning) {
    Write-Host "`nDocker containers detected. Using Docker database..." -ForegroundColor Yellow
    $useDocker = $true
} else {
    Write-Host "`nDocker containers not detected. Checking for local PostgreSQL..." -ForegroundColor Yellow
    $useDocker = $false
    
    # Check if PostgreSQL is accessible on localhost
    try {
        $testConnection = Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
        if (-not $testConnection.TcpTestSucceeded) {
            Write-Host "`nWarning: Cannot connect to PostgreSQL on localhost:5432" -ForegroundColor Yellow
            Write-Host "Please either:" -ForegroundColor Yellow
            Write-Host "  1. Start Docker containers: docker-compose up -d job-automation-db" -ForegroundColor Cyan
            Write-Host "  2. Install and start PostgreSQL locally" -ForegroundColor Cyan
            Write-Host "  3. Update DATABASE_URL in .env file" -ForegroundColor Cyan
            $continue = Read-Host "Continue anyway? (y/n)"
            if ($continue -ne "y") {
                exit 1
            }
        }
    } catch {
        Write-Host "Could not test PostgreSQL connection. Continuing..." -ForegroundColor Yellow
    }
}

# Install dependencies
Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing dependencies" -ForegroundColor Red
    exit 1
}

# Set database URL based on environment
if ($useDocker) {
    $env:DATABASE_URL = "postgresql://jobautomation:password@job-automation-db:5432/jobautomation"
    Write-Host "Using Docker database URL" -ForegroundColor Green
} else {
    # Use port 5433 if database is in Docker (exposed port), 5432 for local PostgreSQL
    $env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"
    Write-Host "Using localhost database URL (port 5433 for Docker)" -ForegroundColor Green
}

# Run migrations
Write-Host "`nRunning database migrations..." -ForegroundColor Yellow
alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nError running migrations. Common issues:" -ForegroundColor Red
    Write-Host "  - Database not running" -ForegroundColor Yellow
    Write-Host "  - Wrong DATABASE_URL (check .env file)" -ForegroundColor Yellow
    Write-Host "  - Database doesn't exist (create it first)" -ForegroundColor Yellow
    Write-Host "`nTo create database:" -ForegroundColor Cyan
    Write-Host "  psql -U postgres -c 'CREATE DATABASE jobautomation;'" -ForegroundColor White
    Write-Host "  psql -U postgres -c 'CREATE USER jobautomation WITH PASSWORD ''password'';'" -ForegroundColor White
    Write-Host "  psql -U postgres -c 'GRANT ALL PRIVILEGES ON DATABASE jobautomation TO jobautomation;'" -ForegroundColor White
    exit 1
}

# Initialize skill profile
Write-Host "`nInitializing skill profile..." -ForegroundColor Yellow
python scripts/init_skill_profile.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error initializing skill profile" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Setup complete!" -ForegroundColor Green
Write-Host "`nYou can now start the service with:" -ForegroundColor Green
Write-Host "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Cyan
Write-Host "`nOr use Docker:" -ForegroundColor Green
Write-Host "  docker-compose up -d" -ForegroundColor Cyan

