# PowerShell script to start Docker service
Write-Host "Checking Docker Desktop status..." -ForegroundColor Cyan

# Check if Docker is running
# Use try-catch for more reliable error handling
$dockerRunning = $false
try {
    $null = docker ps 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $dockerRunning = $true
    }
} catch {
    $dockerRunning = $false
}

# Also check if the error message indicates Docker isn't running
$dockerCheck = docker ps 2>&1
if ($dockerCheck -match "dockerDesktopLinuxEngine|Cannot connect|daemon") {
    $dockerRunning = $false
}

if (-not $dockerRunning) {
    Write-Host "[FAIL] Docker Desktop is not running" -ForegroundColor Red
    if ($dockerCheck) {
        Write-Host "Error: $dockerCheck" -ForegroundColor Red
    }
    Write-Host "`nPlease start Docker Desktop and try again:" -ForegroundColor Yellow
    Write-Host "  1. Open Docker Desktop from Start menu" -ForegroundColor Yellow
    Write-Host "  2. Wait for it to fully start (look for whale icon in system tray)" -ForegroundColor Yellow
    Write-Host "  3. Verify it's running: docker ps (should not show errors)" -ForegroundColor Yellow
    Write-Host "  4. Run this script again" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "[OK] Docker Desktop is running" -ForegroundColor Green
}

Write-Host "`nChecking service container status..." -ForegroundColor Cyan

# Check if container exists and is running
$container = docker ps -a --filter "name=job-automation-service" --format "{{.Names}} {{.Status}}"
if ($container) {
    if ($container -match "Up") {
        Write-Host "[OK] Service container is running" -ForegroundColor Green
        Write-Host "  $container"
    } else {
        Write-Host "[INFO] Service container exists but is stopped" -ForegroundColor Yellow
        Write-Host "  $container"
        Write-Host "`nStarting container..." -ForegroundColor Cyan
        docker start job-automation-service
        Start-Sleep -Seconds 3
    }
} else {
    Write-Host "[INFO] Service container not found. Starting with docker-compose..." -ForegroundColor Yellow
    docker-compose up -d
    Start-Sleep -Seconds 5
}

Write-Host "`nVerifying service health..." -ForegroundColor Cyan
python check_service.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Service is ready!" -ForegroundColor Green
} else {
    Write-Host "`n[WARNING] Service may still be starting. Wait a few seconds and run: python check_service.py" -ForegroundColor Yellow
}

