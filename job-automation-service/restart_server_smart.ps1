# Smart server restart script that ensures .env is loaded
# Usage: .\restart_server_smart.ps1

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "SMART SERVER RESTART" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop existing server
Write-Host "[1/4] Stopping existing server..." -ForegroundColor Yellow
$processes = Get-NetTCPConnection -LocalPort 8004 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($processes) {
    foreach ($processId in $processes) {
        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  Stopping process $processId ($($proc.ProcessName))" -ForegroundColor Yellow
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 3
    # Verify port is free
    $remaining = Get-NetTCPConnection -LocalPort 8004 -ErrorAction SilentlyContinue
    if ($remaining) {
        Write-Host "  WARNING: Port still in use, forcing stop..." -ForegroundColor Yellow
        Get-Process | Where-Object { $_.Id -in $processes } | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    Write-Host "  [OK] Server stopped" -ForegroundColor Green
} else {
    Write-Host "  [OK] No server running" -ForegroundColor Green
}

# Step 2: Verify .env file exists
Write-Host ""
Write-Host "[2/4] Verifying .env file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  [OK] .env file found" -ForegroundColor Green
    $envContent = Get-Content .env -Raw
    if ($envContent -match "ADZUNA_API_ID" -and $envContent -match "ADZUNA_API_KEY") {
        Write-Host "  [OK] Adzuna credentials found in .env" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Adzuna credentials may be missing" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [ERROR] .env file not found!" -ForegroundColor Red
    Write-Host "  Create .env file with API credentials" -ForegroundColor Red
    exit 1
}

# Step 3: Verify Python environment
Write-Host ""
Write-Host "[3/4] Verifying Python environment..." -ForegroundColor Yellow
$pythonExe = "C:\Python313\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "  WARNING: Python 3.13 not found, using system Python" -ForegroundColor Yellow
    $pythonExe = "python"
}

$checkResult = & $pythonExe -c "import pydantic_settings; import httpx; import sqlalchemy; print('OK')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERROR] Required packages not found!" -ForegroundColor Red
    Write-Host "  Error: $checkResult" -ForegroundColor Red
    exit 1
} else {
    Write-Host "  [OK] Dependencies verified" -ForegroundColor Green
}

# Step 4: Start server in background
Write-Host ""
Write-Host "[4/4] Starting server..." -ForegroundColor Yellow
$env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"

# Change to script directory to ensure .env is found
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Verify .env file is accessible
$envPath = Join-Path $scriptDir ".env"
if (Test-Path $envPath) {
    Write-Host "  [OK] .env file found at: $envPath" -ForegroundColor Green
} else {
    Write-Host "  [WARN] .env file not found at: $envPath" -ForegroundColor Yellow
}

Write-Host "  Working directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host "  Python: $pythonExe" -ForegroundColor Cyan
Write-Host "  Starting server in background window..." -ForegroundColor Cyan

# Start server in new window so .env is loaded from current directory
$serverScript = @"
cd 'D:\software\job-automation-service'
`$env:DATABASE_URL = 'postgresql://jobautomation:password@localhost:5433/jobautomation'
Write-Host 'Starting FastAPI server...' -ForegroundColor Green
Write-Host 'Working directory: ' -NoNewline; Write-Host (Get-Location) -ForegroundColor Cyan
Write-Host '.env file location: D:\software\job-automation-service\.env' -ForegroundColor Cyan
if (Test-Path 'D:\software\job-automation-service\.env') {
    Write-Host '[OK] .env file found' -ForegroundColor Green
} else {
    Write-Host '[ERROR] .env file NOT found!' -ForegroundColor Red
}
$pythonExe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $serverScript -WindowStyle Minimized

Write-Host "  [OK] Server starting..." -ForegroundColor Green
Write-Host ""
Write-Host "Waiting 10 seconds for server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Step 5: Verify server started
Write-Host ""
Write-Host "Verifying server health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8004/health" -Method GET -TimeoutSec 5
    Write-Host "  [OK] Server is healthy: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "  [WARN] Server not responding yet: $_" -ForegroundColor Yellow
    Write-Host "  Wait a few more seconds and check manually" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "Server restart complete!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "Test the server with:" -ForegroundColor Cyan
Write-Host "  python test_endpoint_detailed.py" -ForegroundColor White
Write-Host ""

