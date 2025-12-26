# Setup Windows Task Scheduler for Breach Monitoring
# Run this script as Administrator to schedule automatic breach checks

param(
    [string]$Schedule = "Weekly",  # Daily, Weekly, or Custom
    [string]$Time = "09:00",       # Time to run (HH:mm format)
    [string]$DayOfWeek = "Monday"  # For weekly schedule
)

$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$CheckScript = Join-Path $ScriptDir "check_breaches.py"
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source

if (-not $PythonExe) {
    Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
    Write-Host "Please ensure Python is installed and in your PATH" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $CheckScript)) {
    Write-Host "[ERROR] Check script not found: $CheckScript" -ForegroundColor Red
    exit 1
}

# Task name
$TaskName = "HomeCyberRisk-BreachCheck"

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Build action (what to run)
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$CheckScript`"" -WorkingDirectory $ProjectDir

# Build trigger based on schedule
$Trigger = switch ($Schedule.ToLower()) {
    "daily" {
        $timeParts = $Time.Split(':')
        New-ScheduledTaskTrigger -Daily -At "$($timeParts[0]):$($timeParts[1])"
    }
    "weekly" {
        $timeParts = $Time.Split(':')
        $dayOfWeekEnum = [System.DayOfWeek]::$DayOfWeek
        New-ScheduledTaskTrigger -Weekly -DaysOfWeek $dayOfWeekEnum -At "$($timeParts[0]):$($timeParts[1])"
    }
    "custom" {
        Write-Host "For custom schedules, use Task Scheduler GUI" -ForegroundColor Yellow
        $timeParts = $Time.Split(':')
        New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "$($timeParts[0]):$($timeParts[1])"
    }
    default {
        Write-Host "[ERROR] Invalid schedule: $Schedule" -ForegroundColor Red
        Write-Host "Valid options: Daily, Weekly, Custom" -ForegroundColor Yellow
        exit 1
    }
}

# Settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Principal (run as current user)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

# Register the task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Automated breach check for Home Cyber Risk Awareness Server" | Out-Null
    
    Write-Host "`n[OK] Task scheduled successfully!" -ForegroundColor Green
    Write-Host "`nTask Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName"
    Write-Host "  Schedule: $Schedule"
    Write-Host "  Time: $Time"
    if ($Schedule -eq "Weekly") {
        Write-Host "  Day: $DayOfWeek"
    }
    Write-Host "  Script: $CheckScript"
    Write-Host "`nTo manage the task:" -ForegroundColor Yellow
    Write-Host "  - View: Get-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  - Run now: Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  - Remove: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
    Write-Host "  - GUI: taskschd.msc (search for '$TaskName')"
    
} catch {
    Write-Host "[ERROR] Failed to create scheduled task: $_" -ForegroundColor Red
    exit 1
}

