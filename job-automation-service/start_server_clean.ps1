# Start server cleanly after killing all old processes
# Usage: .\start_server_clean.ps1

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "CLEAN SERVER START" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Step 1: Kill all old processes
Write-Host "[1/3] Killing all old server processes..." -ForegroundColor Yellow
& "$PSScriptRoot\kill_all_servers.ps1"

# Step 2: Verify environment
Write-Host ""
Write-Host "[2/3] Verifying environment..." -ForegroundColor Yellow
$pythonExe = "C:\Python313\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "  [WARN] Python 3.13 not found, using system Python" -ForegroundColor Yellow
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

# Verify .env file
$envPath = Join-Path $PSScriptRoot ".env"
if (Test-Path $envPath) {
    Write-Host "  [OK] .env file found" -ForegroundColor Green
} else {
    Write-Host "  [WARN] .env file not found at: $envPath" -ForegroundColor Yellow
}

# Step 3: Start server
Write-Host ""
Write-Host "[3/3] Starting fresh server..." -ForegroundColor Yellow
$env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"

$serverScript = @"
cd 'D:\software\job-automation-service'
`$env:DATABASE_URL = 'postgresql://jobautomation:password@localhost:5433/jobautomation'
Write-Host '========================================' -ForegroundColor Cyan
Write-Host 'STARTING FRESH SERVER INSTANCE' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Cyan
Write-Host 'Working Directory: ' -NoNewline; Write-Host (Get-Location) -ForegroundColor Cyan
Write-Host '.env file: D:\software\job-automation-service\.env' -ForegroundColor Cyan
if (Test-Path 'D:\software\job-automation-service\.env') {
    Write-Host '[OK] .env file found' -ForegroundColor Green
} else {
    Write-Host '[ERROR] .env file NOT found!' -ForegroundColor Red
}
Write-Host 'Python: $pythonExe' -ForegroundColor Cyan
Write-Host 'Starting uvicorn...' -ForegroundColor Yellow
Write-Host ''
$pythonExe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $serverScript -WindowStyle Normal

Write-Host "  [OK] Server starting in new window" -ForegroundColor Green
Write-Host ""
Write-Host "Waiting 15 seconds for server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Step 4: Verify server started
Write-Host ""
Write-Host "Verifying server..." -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8004/health" -TimeoutSec 5
    Write-Host "  [OK] Server is healthy: $($health.status)" -ForegroundColor Green
    
    # Test debug endpoint
    try {
        $debug = Invoke-RestMethod -Uri "http://localhost:8004/debug/credentials" -TimeoutSec 5
        Write-Host "  [OK] Debug endpoint working!" -ForegroundColor Green
        Write-Host "    Has Adzuna Client: $($debug.has_adzuna_client)" -ForegroundColor $(if ($debug.has_adzuna_client) { 'Green' } else { 'Red' })
    } catch {
        Write-Host "  [WARN] Debug endpoint not available yet (may need more time)" -ForegroundColor Yellow
    }
    
    # Test job search
    Write-Host ""
    Write-Host "Testing job search..." -ForegroundColor Cyan
    $body = @{
        query = "python"
        location = "Minneapolis, MN"
        limit = 5
        sources = @("adzuna")
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:8004/api/v1/jobs/search" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
    
    Write-Host "  Jobs found: $($response.count)" -ForegroundColor $(if ($response.count -gt 0) { 'Green' } else { 'Yellow' })
    Write-Host "  Sources searched: $($response.sources_searched -join ', ')" -ForegroundColor Cyan
    
    if ($response.count -gt 0) {
        Write-Host ""
        Write-Host "  [SUCCESS] Server is working!" -ForegroundColor Green
        Write-Host "    First job: $($response.jobs[0].title)" -ForegroundColor Cyan
        Write-Host "    Source: $($response.jobs[0].source)" -ForegroundColor $(if ($response.jobs[0].source) { 'Green' } else { 'Red' })
    } else {
        Write-Host "  [WARN] No jobs returned - check server console for details" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "  [WARN] Server not responding yet: $_" -ForegroundColor Yellow
    Write-Host "  Wait a few more seconds and check the server console window" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "SERVER STARTED" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "Check the SERVER CONSOLE WINDOW for:" -ForegroundColor Cyan
Write-Host "  - '[CONFIG] Loaded .env file' message" -ForegroundColor White
Write-Host "  - 'SERVER STARTUP - CREDENTIALS CHECK' section" -ForegroundColor White
Write-Host "  - 'Has Adzuna Client: True'" -ForegroundColor White
Write-Host "  - No '[DEBUG] Failed to write log' errors" -ForegroundColor White
Write-Host ""

