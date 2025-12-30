# PowerShell script to set camera environment variables

Write-Host "Setting camera environment variables..." -ForegroundColor Yellow

# Required secrets (use strong keys in production)
$env:SECRET_KEY = "temp_secret_key_for_migration_only_min_32_chars_long"
$env:JWT_SECRET_KEY = "temp_jwt_secret_key_for_migration_only_min_32_chars_long"

# Arlo Configuration
$env:ARLO_USERNAME = "schum495@gmail.com"
$env:ARLO_PASSWORD = "Gungho495@"
$env:ARLO_STORAGE_PATH = "D:\CodeRepositories\software\camera_recordings"
$env:ARLO_SYNC_INTERVAL = "300"
$env:ARLO_ENCRYPTION_KEY = "your_encryption_key_here"  # Replace with a strong key

# Database (use PostgreSQL in production, SQLite for testing)
$env:DATABASE_URL = "sqlite:///./test_platform.db"

# Create storage directories
$storagePath = "D:\CodeRepositories\software\camera_recordings"
if (-not (Test-Path $storagePath)) {
    New-Item -ItemType Directory -Path $storagePath -Force | Out-Null
    Write-Host "Created storage directory: $storagePath" -ForegroundColor Green
}

Write-Host "[OK] Environment variables set" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application:" -ForegroundColor Cyan
Write-Host "  python -m uvicorn app.main:app --reload" -ForegroundColor White

