# PowerShell script to restart the uvicorn server
# Usage: .\restart_server.ps1

Write-Host "Stopping any existing uvicorn processes on port 8004..." -ForegroundColor Yellow

# Find and stop processes on port 8004
$processes = Get-NetTCPConnection -LocalPort 8004 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($processes) {
    foreach ($processId in $processes) {
        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($proc -and ($proc.ProcessName -like "*python*" -or $proc.ProcessName -like "*uvicorn*")) {
            Write-Host "  Stopping process $processId ($($proc.ProcessName))" -ForegroundColor Yellow
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 2
}

Write-Host "`nSetting environment variables..." -ForegroundColor Yellow
$env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"

Write-Host "`nStarting uvicorn server..." -ForegroundColor Green
Write-Host "  Command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8004" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow

uvicorn app.main:app --reload --host 0.0.0.0 --port 8004

