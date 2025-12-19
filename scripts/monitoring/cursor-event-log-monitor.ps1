# Cursor Event Log Monitor
# Monitors Windows Event Log for network-related events

param(
    [int]$Interval = 60,  # Check interval in seconds
    [string]$OutputDir = "cursor-event-logs",
    [int]$MaxEvents = 100
)

$ErrorActionPreference = "Stop"

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

# Event log sources to monitor
$EventLogSources = @(
    "Microsoft-Windows-NetworkProfile/Operational",
    "Microsoft-Windows-NetworkLocationWizard/Operational",
    "System"  # For network adapter events
)

function Get-NetworkAdapterEvents {
    param([datetime]$Since)
    
    $events = @()
    
    try {
        # Network adapter state changes
        $adapterEvents = Get-WinEvent -FilterHashtable @{
            LogName = "System"
            ProviderName = "Microsoft-Windows-Kernel-Network"
            StartTime = $Since
        } -ErrorAction SilentlyContinue -MaxEvents $MaxEvents
        
        $events += $adapterEvents | ForEach-Object {
            @{
                TimeCreated = $_.TimeCreated
                Id = $_.Id
                Level = $_.LevelDisplayName
                Message = $_.Message
                Source = "System"
                Type = "NetworkAdapter"
            }
        }
    } catch {
        # Event log may not be available
    }
    
    return $events
}

function Get-FirewallEvents {
    param([datetime]$Since)
    
    $events = @()
    
    try {
        # Windows Firewall events
        $firewallEvents = Get-WinEvent -FilterHashtable @{
            LogName = "Security"
            ProviderName = "Microsoft-Windows-Security-Auditing"
            StartTime = $Since
            Id = @(5156, 5157, 5158)  # Firewall rule events
        } -ErrorAction SilentlyContinue -MaxEvents $MaxEvents
        
        $events += $firewallEvents | ForEach-Object {
            @{
                TimeCreated = $_.TimeCreated
                Id = $_.Id
                Level = $_.LevelDisplayName
                Message = $_.Message
                Source = "Security"
                Type = "Firewall"
            }
        }
    } catch {
        # Event log may not be available or require admin rights
    }
    
    return $events
}

function Get-NetworkProfileEvents {
    param([datetime]$Since)
    
    $events = @()
    
    try {
        $profileEvents = Get-WinEvent -FilterHashtable @{
            LogName = "Microsoft-Windows-NetworkProfile/Operational"
            StartTime = $Since
        } -ErrorAction SilentlyContinue -MaxEvents $MaxEvents
        
        $events += $profileEvents | ForEach-Object {
            @{
                TimeCreated = $_.TimeCreated
                Id = $_.Id
                Level = $_.LevelDisplayName
                Message = $_.Message
                Source = "NetworkProfile"
                Type = "NetworkProfile"
            }
        }
    } catch {
        # Event log may not be available
    }
    
    return $events
}

function Filter-CursorRelatedEvents {
    param([array]$Events)
    
    $cursorKeywords = @("cursor", "api.cursor.com", "cursor.sh", "443", "https")
    
    $filtered = $Events | Where-Object {
        $event = $_
        $message = $event.Message -join " "
        $cursorKeywords | ForEach-Object {
            if ($message -match $_) {
                return $true
            }
        }
        return $false
    }
    
    return $filtered
}

function Monitor-EventLogs {
    Write-Host "Starting Windows Event Log monitoring..."
    Write-Host "Interval: $Interval seconds"
    Write-Host "Output directory: $OutputDir"
    
    $lastCheck = Get-Date
    $allEvents = @()
    
    while ($true) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Write-Host "`n[$timestamp] Checking event logs..."
        
        $events = @()
        
        # Get network adapter events
        Write-Host "  Checking network adapter events..."
        $adapterEvents = Get-NetworkAdapterEvents -Since $lastCheck
        $events += $adapterEvents
        Write-Host "    Found $($adapterEvents.Count) adapter events"
        
        # Get firewall events
        Write-Host "  Checking firewall events..."
        $firewallEvents = Get-FirewallEvents -Since $lastCheck
        $events += $firewallEvents
        Write-Host "    Found $($firewallEvents.Count) firewall events"
        
        # Get network profile events
        Write-Host "  Checking network profile events..."
        $profileEvents = Get-NetworkProfileEvents -Since $lastCheck
        $events += $profileEvents
        Write-Host "    Found $($profileEvents.Count) profile events"
        
        # Filter for Cursor-related events
        $cursorEvents = Filter-CursorRelatedEvents -Events $events
        if ($cursorEvents.Count -gt 0) {
            Write-Host "  Found $($cursorEvents.Count) Cursor-related events"
            $allEvents += $cursorEvents
        }
        
        # Export events
        if ($events.Count -gt 0) {
            $jsonFile = Join-Path $OutputDir "cursor-events-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
            $events | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonFile -Encoding UTF8
        }
        
        $lastCheck = Get-Date
        Start-Sleep -Seconds $Interval
    }
}

# Main execution
try {
    Monitor-EventLogs
} catch {
    Write-Error "Event log monitoring failed: $_"
    Write-Host "Note: Some event logs may require administrator privileges"
    exit 1
}
