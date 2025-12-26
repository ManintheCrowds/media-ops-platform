# Alternative Task Scheduler Setup (GUI Method)
# This script opens Task Scheduler with pre-filled information
# You can manually create the task using the GUI

Write-Host "`n=== Task Scheduler GUI Setup ===" -ForegroundColor Green
Write-Host "`nThis will open Task Scheduler for you to create the task manually." -ForegroundColor Yellow
Write-Host "`nTask Details:" -ForegroundColor Cyan
Write-Host "  Name: HomeCyberRisk-BreachCheck"
Write-Host "  Trigger: Weekly on Monday at 9:00 AM"
Write-Host "  Action: Start a program"
Write-Host "    Program: python"
Write-Host "    Arguments: scripts\check_breaches.py"
Write-Host "    Start in: $PWD"
Write-Host "`nOpening Task Scheduler..." -ForegroundColor Yellow

# Get Python path
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonPath) {
    Write-Host "[WARNING] Python not found in PATH" -ForegroundColor Yellow
    Write-Host "You'll need to find Python manually in Task Scheduler" -ForegroundColor Yellow
} else {
    Write-Host "Python found: $pythonPath" -ForegroundColor Green
}

# Get script path
$scriptPath = Join-Path $PWD "scripts\check_breaches.py"
Write-Host "Script path: $scriptPath" -ForegroundColor Green

# Open Task Scheduler
Start-Process "taskschd.msc"

Write-Host "`nTask Scheduler is now open." -ForegroundColor Green
Write-Host "`nTo create the task:" -ForegroundColor Cyan
Write-Host "1. Click 'Create Basic Task...' in the right panel"
Write-Host "2. Name: HomeCyberRisk-BreachCheck"
Write-Host "3. Description: Automated breach check for Home Cyber Risk Awareness Server"
Write-Host "4. Trigger: Weekly"
Write-Host "5. Day: Monday, Time: 9:00 AM"
Write-Host "6. Action: Start a program"
Write-Host "7. Program/script: $pythonPath"
Write-Host "8. Add arguments: scripts\check_breaches.py"
Write-Host "9. Start in: $PWD"
Write-Host "10. Check 'Open the Properties dialog...' and click Finish"
Write-Host "11. In Properties, check 'Run whether user is logged on or not'"
Write-Host "12. Check 'Run with highest privileges' (optional)"
Write-Host "`nPress any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

