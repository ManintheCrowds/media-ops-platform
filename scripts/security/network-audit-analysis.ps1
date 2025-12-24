# Network Audit Analysis Script
# Analyzes network connections and identifies suspicious patterns
# Run as Administrator for full functionality

param(
    [string]$OutputFile = "network-audit-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt",
    [switch]$Detailed
)

$ErrorActionPreference = "Continue"
$Output = @()

function Write-AuditLog {
    param([string]$Message, [string]$Severity = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Severity) {
        "CRITICAL" { "Red" }
        "WARNING" { "Yellow" }
        "INFO" { "Cyan" }
        default { "White" }
    }
    $logEntry = "[$timestamp] [$Severity] $Message"
    Write-Host $logEntry -ForegroundColor $color
    $script:Output += $logEntry
}

function Get-NetworkDeviceInventory {
    Write-AuditLog "=== Network Device Inventory ===" "INFO"
    
    Write-AuditLog "`n--- ARP Table Analysis ---" "INFO"
    $arpEntries = arp -a | Select-String "192.168.0"
    
    $devices = @()
    foreach ($entry in $arpEntries) {
        if ($entry -match "(\d+\.\d+\.\d+\.\d+)\s+([a-fA-F0-9-]+)") {
            $ip = $matches[1]
            $mac = $matches[2]
            
            # Skip broadcast
            if ($ip -ne "192.168.0.255") {
                $devices += [PSCustomObject]@{
                    IP = $ip
                    MAC = $mac
                }
                Write-AuditLog "Device: $ip - MAC: $mac" "INFO"
            }
        }
    }
    
    Write-AuditLog "`nTotal devices found: $($devices.Count)" "INFO"
    return $devices
}

function Analyze-ExternalConnections {
    Write-AuditLog "`n=== External Connection Analysis ===" "INFO"
    
    $connections = Get-NetTCPConnection -ErrorAction SilentlyContinue | 
        Where-Object { $_.LocalAddress -like "192.168.0.*" -and $_.RemoteAddress -notlike "192.168.0.*" }
    
    # Group by remote IP
    $ipGroups = $connections | Group-Object RemoteAddress | Sort-Object Count -Descending
    
    Write-AuditLog "`n--- Top External IPs by Connection Count ---" "INFO"
    $topIPs = $ipGroups | Select-Object -First 10
    foreach ($group in $topIPs) {
        $percentage = [math]::Round(($group.Count / $connections.Count) * 100, 2)
        Write-AuditLog "$($group.Name): $($group.Count) connections ($percentage%)" "INFO"
        
        # Check if IP is suspicious
        if ($group.Count -gt 50) {
            Write-AuditLog "  WARNING: High connection count - possible suspicious activity" "WARNING"
        }
    }
    
    # Analyze 91.222.185.x range specifically
    $suspiciousRange = $connections | Where-Object { $_.RemoteAddress -like "91.222.185.*" }
    if ($suspiciousRange) {
        Write-AuditLog "`n--- Analysis: 91.222.185.x IP Range ---" "WARNING"
        Write-AuditLog "Total connections to 91.222.185.x: $($suspiciousRange.Count)" "WARNING"
        
        $uniqueIPs = ($suspiciousRange | Select-Object -Unique RemoteAddress).Count
        Write-AuditLog "Unique IPs in range: $uniqueIPs" "WARNING"
        
        # Try to resolve one IP
        try {
            $sampleIP = ($suspiciousRange | Select-Object -First 1).RemoteAddress
            $hostname = [System.Net.Dns]::GetHostEntry($sampleIP).HostName
            Write-AuditLog "Sample hostname: $hostname" "INFO"
        } catch {
            Write-AuditLog "Could not resolve hostname" "INFO"
        }
        
        Write-AuditLog "  NOTE: This IP range appears frequently. Research recommended." "WARNING"
    }
    
    return $ipGroups
}

function Analyze-InternalConnections {
    Write-AuditLog "`n=== Internal Network Connection Analysis ===" "INFO"
    
    $internalConnections = Get-NetTCPConnection -ErrorAction SilentlyContinue | 
        Where-Object { $_.LocalAddress -like "192.168.0.*" -and $_.RemoteAddress -like "192.168.0.*" }
    
    Write-AuditLog "Total internal connections: $($internalConnections.Count)" "INFO"
    
    # Group by remote IP
    $internalGroups = $internalConnections | Group-Object RemoteAddress
    
    foreach ($group in $internalGroups) {
        $remoteIP = $group.Name
        $count = $group.Count
        $ports = ($group.Group | Select-Object -Unique RemotePort) -join ", "
        
        Write-AuditLog "`nConnections to $remoteIP : $count connections on ports: $ports" "INFO"
        
        # Check for suspicious ports
        $suspiciousPorts = @(7680, 445, 139, 135, 3389, 22, 23)
        $foundSuspicious = $false
        foreach ($port in $suspiciousPorts) {
            if ($ports -like "*$port*") {
                $portName = switch ($port) {
                    7680 { "SMB/NetBIOS (possibly)" }
                    445 { "SMB (File Sharing)" }
                    139 { "NetBIOS" }
                    135 { "RPC" }
                    3389 { "RDP (Remote Desktop)" }
                    22 { "SSH" }
                    23 { "Telnet" }
                }
                Write-AuditLog "  Port $port ($portName) detected" "WARNING"
                $foundSuspicious = $true
            }
        }
        
        if ($foundSuspicious) {
            Write-AuditLog "  ACTION: Verify this is expected file sharing activity" "WARNING"
        }
    }
    
    # Check for connections to router
    $routerConnections = $internalConnections | Where-Object { $_.RemoteAddress -eq "192.168.0.1" }
    if ($routerConnections) {
        Write-AuditLog "`n--- Router Connections (192.168.0.1) ---" "INFO"
        $routerPorts = ($routerConnections | Group-Object RemotePort | Sort-Object Count -Descending) | Select-Object -First 5
        foreach ($portGroup in $routerPorts) {
            $portName = switch ($portGroup.Name) {
                443 { "HTTPS (Admin Interface)" }
                53 { "DNS" }
                80 { "HTTP (Admin Interface)" }
                default { "Unknown" }
            }
            Write-AuditLog "Port $($portGroup.Name) ($portName): $($portGroup.Count) connections" "INFO"
        }
    }
    
    return $internalConnections
}

function Test-IPReputation {
    param([string[]]$IPs)
    
    Write-AuditLog "`n=== IP Reputation Check ===" "INFO"
    Write-AuditLog "Note: This requires internet connection and may take time" "INFO"
    
    foreach ($ip in $IPs) {
        Write-AuditLog "`nChecking: $ip" "INFO"
        
        # Try AbuseIPDB lookup (requires API key - placeholder)
        Write-AuditLog "  Manual check recommended: https://www.abuseipdb.com/check/$ip" "INFO"
        Write-AuditLog "  Manual check recommended: https://www.virustotal.com/gui/ip-address/$ip" "INFO"
        
        # Try basic reverse DNS
        try {
            $hostname = [System.Net.Dns]::GetHostEntry($ip).HostName
            Write-AuditLog "  Hostname: $hostname" "INFO"
            
            # Check for suspicious patterns
            if ($hostname -match "tor|proxy|vpn|anonymous|malware|botnet") {
                Write-AuditLog "  CRITICAL: Suspicious hostname pattern detected!" "CRITICAL"
            }
        } catch {
            Write-AuditLog "  Could not resolve hostname" "INFO"
        }
    }
}

function Get-ProcessNetworkActivity {
    Write-AuditLog "`n=== Process Network Activity Analysis ===" "INFO"
    
    $connections = Get-NetTCPConnection -ErrorAction SilentlyContinue | 
        Where-Object { $_.State -eq "Established" -and $_.LocalAddress -like "192.168.0.*" }
    
    $processGroups = $connections | Group-Object OwningProcess
    
    Write-AuditLog "`n--- Top Network-Active Processes ---" "INFO"
    $topProcesses = $processGroups | Sort-Object Count -Descending | Select-Object -First 10
    
    foreach ($procGroup in $topProcesses) {
        try {
            $proc = Get-Process -Id $procGroup.Name -ErrorAction SilentlyContinue
            if ($proc) {
                $procName = $proc.ProcessName
                $procPath = $proc.Path
                $connCount = $procGroup.Count
                
                Write-AuditLog "`n$procName (PID: $($procGroup.Name))" "INFO"
                Write-AuditLog "  Connections: $connCount" "INFO"
                Write-AuditLog "  Path: $procPath" "INFO"
                
                # Check for suspicious process locations
                if ($procPath -notlike "C:\Windows\*" -and $procPath -notlike "C:\Program Files\*" -and $procPath -notlike "C:\Program Files (x86)\*") {
                    Write-AuditLog "  WARNING: Process running from unusual location" "WARNING"
                }
            }
        } catch {
            Write-AuditLog "Process ID $($procGroup.Name): Could not retrieve details" "INFO"
        }
    }
}

function Get-SecurityRecommendations {
    Write-AuditLog "`n=== Security Recommendations ===" "INFO"
    
    $recommendations = @(
        "1. Verify all devices in ARP table are known and authorized",
        "2. Research 91.222.185.x IP range - high connection volume detected",
        "3. Review connections to 192.168.0.43 on port 7680 (SMB/NetBIOS)",
        "4. Check router admin panel for full device list",
        "5. Enable router logging and review for suspicious activity",
        "6. Consider enabling MAC address filtering on router",
        "7. Review firewall rules on router",
        "8. Check for unauthorized port forwarding rules",
        "9. Verify DNS settings haven't been changed",
        "10. Run full antivirus scan on all devices",
        "11. Check for unauthorized software installations",
        "12. Review Windows Firewall rules",
        "13. Check for suspicious scheduled tasks",
        "14. Review Windows Event Logs for security events",
        "15. Consider network monitoring tool for ongoing surveillance"
    )
    
    foreach ($rec in $recommendations) {
        Write-AuditLog $rec "INFO"
    }
}

function Get-EventLogSecurity {
    Write-AuditLog "`n=== Windows Security Event Log Analysis ===" "INFO"
    
    try {
        # Check for failed login attempts
        $failedLogins = Get-WinEvent -FilterHashtable @{
            LogName = 'Security'
            ID = 4625  # Failed logon
            StartTime = (Get-Date).AddHours(-24)
        } -ErrorAction SilentlyContinue | Measure-Object
        
        if ($failedLogins.Count -gt 0) {
            Write-AuditLog "Failed login attempts (last 24h): $($failedLogins.Count)" "WARNING"
            if ($failedLogins.Count -gt 10) {
                Write-AuditLog "  CRITICAL: High number of failed logins - possible brute force attack" "CRITICAL"
            }
        } else {
            Write-AuditLog "No failed login attempts in last 24 hours" "INFO"
        }
        
        # Check for account lockouts
        $lockouts = Get-WinEvent -FilterHashtable @{
            LogName = 'Security'
            ID = 4740  # Account lockout
            StartTime = (Get-Date).AddHours(-24)
        } -ErrorAction SilentlyContinue | Measure-Object
        
        if ($lockouts.Count -gt 0) {
            Write-AuditLog "Account lockouts (last 24h): $($lockouts.Count)" "WARNING"
        }
        
    } catch {
        Write-AuditLog "Could not access Security Event Log (may require Administrator)" "WARNING"
    }
}

# Main execution
Write-AuditLog "==========================================" "INFO"
Write-AuditLog "Network Security Audit Report" "INFO"
Write-AuditLog "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "INFO"
Write-AuditLog "Computer: $env:COMPUTERNAME" "INFO"
Write-AuditLog "User: $env:USERNAME" "INFO"
Write-AuditLog "==========================================" "INFO"

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-AuditLog "WARNING: Not running as Administrator. Some checks may be limited." "WARNING"
}

$devices = Get-NetworkDeviceInventory
$externalIPs = Analyze-ExternalConnections
$internalConnections = Analyze-InternalConnections
Get-ProcessNetworkActivity
Get-EventLogSecurity

# Check top suspicious IPs
$topSuspiciousIPs = ($externalIPs | Where-Object { $_.Count -gt 20 } | Select-Object -First 5).Name
if ($topSuspiciousIPs) {
    Test-IPReputation -IPs $topSuspiciousIPs
}

Get-SecurityRecommendations

Write-AuditLog "`n==========================================" "INFO"
Write-AuditLog "Audit Complete" "INFO"
Write-AuditLog "Report saved to: $OutputFile" "INFO"
Write-AuditLog "==========================================" "INFO"

# Save output to file
$Output | Out-File -FilePath $OutputFile -Encoding UTF8
Write-Host "`nReport saved to: $OutputFile" -ForegroundColor Green

# Display critical findings summary
Write-Host "`n=== CRITICAL FINDINGS SUMMARY ===" -ForegroundColor Yellow

$criticalCount = ($Output | Select-String "CRITICAL").Count
$warningCount = ($Output | Select-String "WARNING").Count

Write-Host "Critical issues: $criticalCount" -ForegroundColor $(if ($criticalCount -gt 0) { "Red" } else { "Green" })
Write-Host "Warnings: $warningCount" -ForegroundColor $(if ($warningCount -gt 0) { "Yellow" } else { "Green" })

if ($criticalCount -gt 0 -or $warningCount -gt 5) {
    Write-Host "`nReview the full report for details: $OutputFile" -ForegroundColor Red
}

