# Fix server credentials by setting environment variables explicitly
# This ensures the server process has access to API keys even if .env isn't loaded

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "FIX SERVER CREDENTIALS" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Stop existing server
Write-Host "[1/3] Stopping existing server..." -ForegroundColor Yellow
$procs = Get-NetTCPConnection -LocalPort 8004 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($procs) {
    foreach ($p in $procs) {
        Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
        Write-Host "  Stopped process $p" -ForegroundColor Yellow
    }
    Start-Sleep -Seconds 2
}
Write-Host "[OK] Server stopped" -ForegroundColor Green
Write-Host ""

# Set environment variables explicitly
Write-Host "[2/3] Setting environment variables..." -ForegroundColor Yellow
$env:ADZUNA_API_ID = "a4a7673a"
$env:ADZUNA_API_KEY = "f6163b196847b9d597b71b9df86fdd2d"
$env:JSEARCH_API_KEY = "ak_r2baolkzsanqqwhfditlmydwa9jtcyei2qynhxqmqfdvvw4"
$env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"

Write-Host "  ADZUNA_API_ID: $env:ADZUNA_API_ID" -ForegroundColor Cyan
Write-Host "  ADZUNA_API_KEY: Set" -ForegroundColor Cyan
Write-Host "  JSEARCH_API_KEY: Set" -ForegroundColor Cyan
Write-Host "[OK] Environment variables set" -ForegroundColor Green
Write-Host ""

# Start server with environment variables
Write-Host "[3/3] Starting server with explicit credentials..." -ForegroundColor Yellow
$pythonExe = "C:\Python313\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$serverScript = @"
cd 'D:\software\job-automation-service'
`$env:ADZUNA_API_ID = 'a4a7673a'
`$env:ADZUNA_API_KEY = 'f6163b196847b9d597b71b9df86fdd2d'
`$env:JSEARCH_API_KEY = 'ak_r2baolkzsanqqwhfditlmydwa9jtcyei2qynhxqmqfdvvw4'
`$env:DATABASE_URL = 'postgresql://jobautomation:password@localhost:5433/jobautomation'
Write-Host 'Starting server with explicit environment variables...' -ForegroundColor Green
Write-Host 'ADZUNA_API_ID: ' -NoNewline; Write-Host `$env:ADZUNA_API_ID -ForegroundColor Cyan
Write-Host 'ADZUNA_API_KEY: Set' -ForegroundColor Cyan
$pythonExe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $serverScript -WindowStyle Normal

Write-Host "[OK] Server starting in new window" -ForegroundColor Green
Write-Host ""
Write-Host "Waiting 12 seconds for server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 12

# Test server
Write-Host ""
Write-Host "Testing server..." -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8004/health" -TimeoutSec 5
    Write-Host "[OK] Server is healthy: $($health.status)" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Testing job search..." -ForegroundColor Cyan
    $body = @{
        query = "python"
        location = "Minneapolis, MN"
        limit = 5
        sources = @("adzuna")
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:8004/api/v1/jobs/search" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
    
    Write-Host "Jobs found: $($response.count)" -ForegroundColor $(if ($response.count -gt 0) { 'Green' } else { 'Yellow' })
    Write-Host "Sources searched: $($response.sources_searched -join ', ')" -ForegroundColor Cyan
    
    if ($response.count -gt 0) {
        Write-Host ""
        Write-Host "=" * 80 -ForegroundColor Green
        Write-Host "SUCCESS! Server is returning jobs!" -ForegroundColor Green
        Write-Host "=" * 80 -ForegroundColor Green
        Write-Host ""
        Write-Host "First job: $($response.jobs[0].title)" -ForegroundColor Cyan
        Write-Host "Company: $($response.jobs[0].company)" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "[WARN] Still returning 0 jobs" -ForegroundColor Yellow
        Write-Host "Check the server console window for startup messages" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "Done! Check the server console window for credential status." -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

