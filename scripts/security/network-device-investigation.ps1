# Network Device Investigation Script
# Helps identify and investigate suspicious devices on the network
# Run as Administrator for full functionality

param(
    [string]$RouterIP = "192.168.0.1",
    [string]$NetworkRange = "192.168.0.0/24",
    [string]$OutputFile = "network-investigation-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
)

$ErrorActionPreference = "Continue"
$Output = @()

function Write-InvestigationLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"
    Write-Host $logEntry
    $script:Output += $logEntry
}

function Get-NetworkDevices {
    Write-InvestigationLog "=== Network Device Discovery ==="
    
    Write-InvestigationLog "Scanning network range: $NetworkRange"
    
    # Get ARP table
    Write-InvestigationLog "`n--- ARP Table (Active Devices) ---"
    $arpEntries = arp -a | Select-String "192.168.0"
    foreach ($entry in $arpEntries) {
        Write-InvestigationLog $entry.ToString()
    }
    
    # Get active TCP connections
    Write-InvestigationLog "`n--- Active TCP Connections ---"
    $connections = Get-NetTCPConnection -ErrorAction SilentlyContinue | 
        Where-Object { $_.State -eq "Established" -and $_.LocalAddress -like "192.168.0.*" } |
        Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess
    
    foreach ($conn in $connections) {
        $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        $processName = if ($process) { $process.ProcessName } else { "Unknown" }
        Write-InvestigationLog "$($conn.LocalAddress):$($conn.LocalPort) -> $($conn.RemoteAddress):$($conn.RemotePort) [$processName]"
    }
    
    # Get network adapters
    Write-InvestigationLog "`n--- Network Adapters ---"
    $adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" }
    foreach ($adapter in $adapters) {
        $ipConfig = Get-NetIPAddress -InterfaceIndex $adapter.InterfaceIndex -ErrorAction SilentlyContinue
        Write-InvestigationLog "$($adapter.Name): $($adapter.MacAddress) - $($ipConfig.IPAddress)"
    }
}

function Test-RouterAccess {
    param([string]$RouterIP)
    
    Write-InvestigationLog "`n=== Router Connectivity Test ==="
    
    # Ping test
    Write-InvestigationLog "Testing connectivity to router: $RouterIP"
    $ping = Test-Connection -ComputerName $RouterIP -Count 2 -ErrorAction SilentlyContinue
    if ($ping) {
        Write-InvestigationLog "Router is reachable"
    } else {
        Write-InvestigationLog "WARNING: Router is NOT reachable"
    }
    
    # Check if router web interface is accessible
    Write-InvestigationLog "`nTesting router web interface..."
    try {
        $response = Invoke-WebRequest -Uri "http://$RouterIP" -TimeoutSec 5 -ErrorAction Stop
        Write-InvestigationLog "Router web interface is accessible (Status: $($response.StatusCode))"
        Write-InvestigationLog "Router Title: $($response.ParsedHtml.title)"
    } catch {
        Write-InvestigationLog "Router web interface test: $($_.Exception.Message)"
    }
}

function Get-SuspiciousDevices {
    Write-InvestigationLog "`n=== Suspicious Device Detection ==="
    
    # Check for devices with suspicious names
    $suspiciousNames = @("Roko_Basilisk", "Basilisk", "Unknown", "Device", "Android", "iPhone")
    
    Write-InvestigationLog "Checking for devices with suspicious names..."
    
    # Get DHCP leases if accessible (requires router access)
    Write-InvestigationLog "Note: To see full device list, check router admin panel at http://$RouterIP"
    Write-InvestigationLog "Look for devices named: Roko_Basilisk 2"
    
    # Check for unusual network activity
    Write-InvestigationLog "`n--- Network Activity Summary ---"
    $recentConnections = Get-NetTCPConnection -ErrorAction SilentlyContinue | 
        Where-Object { $_.State -eq "Established" } |
        Measure-Object
    
    Write-InvestigationLog "Active connections: $($recentConnections.Count)"
}

function Get-SystemSecurityStatus {
    Write-InvestigationLog "`n=== System Security Status ==="
    
    # Check Windows Firewall
    $firewall = Get-NetFirewallProfile
    Write-InvestigationLog "`n--- Windows Firewall Status ---"
    foreach ($profile in $firewall) {
        $status = if ($profile.Enabled) { "ENABLED" } else { "DISABLED" }
        Write-InvestigationLog "$($profile.Name): $status"
    }
    
    # Check for antivirus
    Write-InvestigationLog "`n--- Antivirus Status ---"
    $antivirus = Get-CimInstance -Namespace "root\SecurityCenter2" -ClassName "AntiVirusProduct" -ErrorAction SilentlyContinue
    if ($antivirus) {
        foreach ($av in $antivirus) {
            Write-InvestigationLog "$($av.displayName): $($av.productState)"
        }
    } else {
        Write-InvestigationLog "Could not detect antivirus status"
    }
    
    # Check for suspicious processes
    Write-InvestigationLog "`n--- Network-Active Processes ---"
    $networkProcesses = Get-NetTCPConnection -ErrorAction SilentlyContinue |
        Where-Object { $_.State -eq "Established" } |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object {
            $proc = Get-Process -Id $_ -ErrorAction SilentlyContinue
            if ($proc) {
                Write-InvestigationLog "$($proc.ProcessName) (PID: $($proc.Id)) - $($proc.Path)"
            }
        }
}

function Get-Recommendations {
    Write-InvestigationLog "`n=== Security Recommendations ==="
    
    $recommendations = @(
        "1. IMMEDIATELY change router admin password",
        "2. Change Wi-Fi password (WPA2/WPA3)",
        "3. Access router admin panel at http://$RouterIP",
        "4. Check 'Connected Devices' or 'DHCP Client List'",
        "5. Look for device named 'Roko_Basilisk 2'",
        "6. Note the MAC address and IP of suspicious device",
        "7. Block the device using MAC address filtering",
        "8. Disable remote management on router",
        "9. Disable WPS (Wi-Fi Protected Setup)",
        "10. Update router firmware",
        "11. Run full antivirus scan on all devices",
        "12. Change passwords for all online accounts",
        "13. Enable network monitoring",
        "14. Review router logs for unauthorized access",
        "15. Consider contacting CenturyLink support"
    )
    
    foreach ($rec in $recommendations) {
        Write-InvestigationLog $rec
    }
}

# Main execution
Write-InvestigationLog "=========================================="
Write-InvestigationLog "Network Device Investigation Report"
Write-InvestigationLog "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-InvestigationLog "Computer: $env:COMPUTERNAME"
Write-InvestigationLog "User: $env:USERNAME"
Write-InvestigationLog "=========================================="

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-InvestigationLog "`nWARNING: Not running as Administrator. Some checks may be limited."
    Write-InvestigationLog "For full functionality, run PowerShell as Administrator."
}

Get-NetworkDevices
Test-RouterAccess -RouterIP $RouterIP
Get-SuspiciousDevices
Get-SystemSecurityStatus
Get-Recommendations

Write-InvestigationLog "`n=========================================="
Write-InvestigationLog "Investigation Complete"
Write-InvestigationLog "Report saved to: $OutputFile"
Write-InvestigationLog "=========================================="

# Save output to file
$Output | Out-File -FilePath $OutputFile -Encoding UTF8
Write-Host "`nReport saved to: $OutputFile" -ForegroundColor Green

# Display summary
Write-Host "`n=== QUICK ACTION CHECKLIST ===" -ForegroundColor Yellow
Write-Host "1. Access router: http://$RouterIP" -ForegroundColor Cyan
Write-Host "2. Check connected devices list" -ForegroundColor Cyan
Write-Host "3. Look for 'Roko_Basilisk 2' device" -ForegroundColor Cyan
Write-Host "4. Change router password immediately" -ForegroundColor Red
Write-Host "5. Block suspicious device MAC address" -ForegroundColor Red
Write-Host "`nSee full report: $OutputFile" -ForegroundColor Green

