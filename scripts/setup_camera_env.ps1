# PowerShell script to set camera environment variables

Write-Host "Setting camera environment variables..." -ForegroundColor Yellow

# Load environment variables from .env file if it exists
$envFile = "D:\software\.env"
if (Test-Path $envFile) {
    Write-Host "Loading environment variables from .env file..." -ForegroundColor Cyan
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, 'Process')
        }
    }
    Write-Host "[OK] Environment variables loaded from .env" -ForegroundColor Green
} else {
    Write-Host "[WARN] .env file not found at $envFile" -ForegroundColor Yellow
    Write-Host "Please create .env file with required variables:" -ForegroundColor Yellow
    Write-Host "  - SECRET_KEY" -ForegroundColor White
    Write-Host "  - JWT_SECRET_KEY" -ForegroundColor White
    Write-Host "  - ARLO_USERNAME" -ForegroundColor White
    Write-Host "  - ARLO_PASSWORD" -ForegroundColor White
    Write-Host "  - DATABASE_URL" -ForegroundColor White
    Write-Host ""
    Write-Host "See .env.example for template" -ForegroundColor Cyan
}

# Set defaults if not already set from .env
if (-not $env:SECRET_KEY) {
    Write-Host "[WARN] SECRET_KEY not set. Using temporary key for development only." -ForegroundColor Yellow
    $env:SECRET_KEY = "temp_secret_key_for_migration_only_min_32_chars_long"
}

if (-not $env:JWT_SECRET_KEY) {
    Write-Host "[WARN] JWT_SECRET_KEY not set. Using temporary key for development only." -ForegroundColor Yellow
    $env:JWT_SECRET_KEY = "temp_jwt_secret_key_for_migration_only_min_32_chars_long"
}

if (-not $env:ARLO_STORAGE_PATH) {
    $env:ARLO_STORAGE_PATH = "D:\software\camera_recordings"
}

if (-not $env:ARLO_SYNC_INTERVAL) {
    $env:ARLO_SYNC_INTERVAL = "300"
}

# Database (use PostgreSQL in production, SQLite for testing)
if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "sqlite:///./test_platform.db"
}

# Create storage directories
$storagePath = "D:\portfolio-harness\software\camera_recordings"
if (-not (Test-Path $storagePath)) {
    New-Item -ItemType Directory -Path $storagePath -Force | Out-Null
    Write-Host "Created storage directory: $storagePath" -ForegroundColor Green
}

Write-Host "[OK] Environment variables set" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application:" -ForegroundColor Cyan
Write-Host "  python -m uvicorn app.main:app --reload" -ForegroundColor White

