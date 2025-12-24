# PowerShell script to restart server and test Adzuna endpoint
# Usage: .\restart_and_test.ps1

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Restarting Server and Testing Adzuna API" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Stop existing server
Write-Host "Stopping existing server..." -ForegroundColor Yellow
$processes = Get-NetTCPConnection -LocalPort 8004 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($processes) {
    foreach ($processId in $processes) {
        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($proc -and ($proc.ProcessName -like "*python*" -or $proc.ProcessName -like "*uvicorn*")) {
            Write-Host "  Stopping process $processId" -ForegroundColor Yellow
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 3
}

# Set environment
$env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"

# Start server in background
Write-Host "`nStarting server..." -ForegroundColor Green
$job = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    $env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
}

# Wait for server to start
Write-Host "Waiting for server to start..." -ForegroundColor Yellow
$maxAttempts = 15
$attempt = 0
$serverReady = $false

do {
    $attempt++
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8004/health" -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] Server is ready!" -ForegroundColor Green
            $serverReady = $true
            break
        }
    } catch {
        Write-Host "  Attempt $attempt/$maxAttempts..." -ForegroundColor Gray
    }
} while ($attempt -lt $maxAttempts)

if (-not $serverReady) {
    Write-Host "[ERROR] Server did not start in time" -ForegroundColor Red
    Stop-Job $job -ErrorAction SilentlyContinue
    Remove-Job $job -ErrorAction SilentlyContinue
    exit 1
}

# Test the endpoint
Write-Host "`nTesting Adzuna API endpoint..." -ForegroundColor Cyan
python test_adzuna_endpoint.py

Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "Server is running in background job" -ForegroundColor Yellow
Write-Host "To stop: Stop-Job -Id $($job.Id); Remove-Job -Id $($job.Id)" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan

