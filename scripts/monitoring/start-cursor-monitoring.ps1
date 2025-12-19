# Start Cursor Monitoring System
# This script starts all monitoring components

Write-Host "Starting Cursor Monitoring System..." -ForegroundColor Green

# Check if Cursor is running
$cursorProcess = Get-Process -Name "Cursor" -ErrorAction SilentlyContinue
if (-not $cursorProcess) {
    Write-Host "Warning: Cursor IDE is not running. Monitoring will start but may not collect data." -ForegroundColor Yellow
}

# Create output directories
$directories = @("cursor-metrics", "cursor-quality-metrics", "cursor-event-logs")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Cyan
    }
}

# Start Process Monitor
Write-Host "`nStarting Process Monitor..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..\..'; .\scripts\monitoring\cursor-process-monitor.ps1 -Interval 5 -OutputDir 'cursor-metrics'" -WindowStyle Minimized

# Start Quality Monitor
Write-Host "Starting Connection Quality Monitor..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..\..'; .\scripts\monitoring\cursor-connection-quality.ps1 -Endpoints @('api.cursor.com') -Interval 30 -OutputDir 'cursor-quality-metrics'" -WindowStyle Minimized

# Start Event Log Monitor (optional, requires admin)
Write-Host "Starting Event Log Monitor (optional)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..\..'; .\scripts\monitoring\cursor-event-log-monitor.ps1 -Interval 60 -OutputDir 'cursor-event-logs'" -WindowStyle Minimized

# Start Prometheus Exporter
Write-Host "`nStarting Prometheus Exporter..." -ForegroundColor Cyan
$exporterPath = Join-Path $PSScriptRoot "..\..\monitoring\cursor-exporter\cursor_exporter.py"
if (Test-Path $exporterPath) {
    Start-Process python -ArgumentList $exporterPath, "--port", "9101", "--interval", "30" -WindowStyle Minimized
    Write-Host "Exporter started on port 9101" -ForegroundColor Green
    Write-Host "Metrics endpoint: http://localhost:9101/metrics" -ForegroundColor Cyan
    Write-Host "Health endpoint: http://localhost:9101/health" -ForegroundColor Cyan
} else {
    Write-Host "Error: Exporter not found at $exporterPath" -ForegroundColor Red
}

Write-Host "`nMonitoring system started!" -ForegroundColor Green
Write-Host "`nTo verify:" -ForegroundColor Yellow
Write-Host "  1. Check exporter: http://localhost:9101/health" -ForegroundColor White
Write-Host "  2. Check metrics: http://localhost:9101/metrics" -ForegroundColor White
Write-Host "  3. Import dashboard in Grafana: monitoring/grafana/dashboards/cursor-connections.json" -ForegroundColor White
Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
