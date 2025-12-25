# PowerShell script to restart the uvicorn server
# Usage: .\restart_server.ps1

Write-Host "Stopping any existing uvicorn processes on port 8004..." -ForegroundColor Yellow

# Find and stop processes on port 8004
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
        Write-Host "  WARNING: Port 8004 still in use. Trying again..." -ForegroundColor Yellow
        foreach ($processId in $processes) {
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    }
}

Write-Host "`nSetting environment variables..." -ForegroundColor Yellow
$env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"

# Verify Python environment has required packages
Write-Host "`nVerifying Python environment..." -ForegroundColor Yellow
$pythonExe = "C:\Python313\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "WARNING: Python 3.13 not found, using system Python" -ForegroundColor Yellow
    $pythonExe = "python"
}

$checkResult = & $pythonExe -c "import pydantic_settings; import httpx; import sqlalchemy; print('OK')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Required packages not found in Python environment!" -ForegroundColor Red
    Write-Host "  Error: $checkResult" -ForegroundColor Red
    Write-Host "`nInstall dependencies with:" -ForegroundColor Yellow
    Write-Host "  python install_dependencies_fixed.py" -ForegroundColor Cyan
    Write-Host "  python -m pip install --only-binary :all: psycopg2-binary" -ForegroundColor Cyan
    exit 1
} else {
    Write-Host "  Dependencies verified: OK" -ForegroundColor Green
}

Write-Host "`nStarting uvicorn server..." -ForegroundColor Green

# Use explicit Python 3.13 path to ensure correct environment
$pythonExe = "C:\Python313\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python 3.13 not found at $pythonExe" -ForegroundColor Red
    Write-Host "Using system Python instead..." -ForegroundColor Yellow
    $pythonExe = "python"
}

Write-Host "  Using Python: $pythonExe" -ForegroundColor Cyan
Write-Host "  Command: $pythonExe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8004" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow

& $pythonExe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8004

