# PURPOSE: Phase 1 - Comprehensive diagnostic script for Darktide SSL timeout issues
# DEPENDENCIES: darktide_common.ps1, Windows PowerShell
# MODIFICATION NOTES: Implements all diagnostic recommendations from review document

param(
    [switch]$Verbose,
    [string]$OutputPath
)

# Import common utilities
$commonPath = Join-Path $PSScriptRoot "darktide_common.ps1"
if (Test-Path $commonPath) {
    . $commonPath
} else {
    Write-Host "ERROR: darktide_common.ps1 not found!" -ForegroundColor Red
    exit 1
}

Write-Host "=== Darktide Diagnostic Phase 1 ===" -ForegroundColor Cyan
Write-Host ""

# Initialize findings collection
$findings = @{
    "Schannel Logging" = @()
    "Network Packet Capture" = @()
    "Event Log Analysis" = @()
    "Process Network Comparison" = @()
    "Network Connectivity" = @()
    "System Configuration" = @()
}

$darktidePath = Get-DarktidePath
if (-not $darktidePath) {
    Write-Log "Darktide.exe not found in standard locations" -Level Error
    exit 1
}

Write-Log "Found Darktide at: $darktidePath" -Level Success
Write-Host ""

# ============================================================================
# 1.1 Schannel Logging Setup
# ============================================================================

Write-Host "1.1 Schannel Logging Setup" -ForegroundColor Green
Write-Host ""

try {
    # Enable schannel operational logging
    $result = wevtutil sl Microsoft-Windows-Schannel/Operational /e:true 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Schannel operational logging enabled" -Level Success
        $findings["Schannel Logging"] += @{
            Title = "Schannel Operational Logging"
            Description = "Successfully enabled schannel operational logging"
            Status = "Success"
        }
    } else {
        Write-Log "Could not enable schannel operational logging: $result" -Level Warning
        $findings["Schannel Logging"] += @{
            Title = "Schannel Operational Logging"
            Description = "Could not enable: $result. May require Administrator privileges."
            Status = "Warning"
        }
    }
} catch {
    Write-Log "Error enabling schannel logging: $_" -Level Error
    $findings["Schannel Logging"] += @{
        Title = "Schannel Operational Logging"
        Description = "Error: $_"
        Status = "Error"
    }
}

# Check if analytic logging is available
try {
    $analyticLog = Get-WinEvent -ListLog "Microsoft-Windows-Schannel/Analytic" -ErrorAction SilentlyContinue
    if ($analyticLog) {
        Write-Log "Schannel analytic log available" -Level Info
        $findings["Schannel Logging"] += @{
            Title = "Schannel Analytic Logging"
            Description = "Analytic log is available (may require manual enable)"
            Status = "Info"
        }
    }
} catch {
    Write-Log "Schannel analytic log not available" -Level Info
}

# Export current schannel configuration
try {
    $schannelConfig = @{
        OperationalEnabled = (Get-WinEvent -ListLog "Microsoft-Windows-Schannel/Operational" -ErrorAction SilentlyContinue).IsEnabled
        OperationalMaxSize = (Get-WinEvent -ListLog "Microsoft-Windows-Schannel/Operational" -ErrorAction SilentlyContinue).MaximumSizeInBytes
    }
    Write-Log "Schannel configuration exported" -Level Success
} catch {
    Write-Log "Could not export schannel configuration: $_" -Level Warning
}

Write-Host ""

# ============================================================================
# 1.2 Network Packet Capture Setup
# ============================================================================

Write-Host "1.2 Network Packet Capture Setup" -ForegroundColor Green
Write-Host ""

$backendConfig = Get-BackendConfiguration
$captureInstructions = @()

# Check for Wireshark
$wiresharkPaths = @(
    "${env:ProgramFiles}\Wireshark\wireshark.exe",
    "${env:ProgramFiles(x86)}\Wireshark\wireshark.exe"
)

$wiresharkFound = $false
foreach ($path in $wiresharkPaths) {
    if (Test-Path $path) {
        Write-Log "Wireshark found at: $path" -Level Success
        $wiresharkFound = $true
        $findings["Network Packet Capture"] += @{
            Title = "Wireshark Available"
            Description = "Wireshark is installed and available for packet capture"
            Status = "Success"
        }
        break
    }
}

if (-not $wiresharkFound) {
    Write-Log "Wireshark not found" -Level Warning
    $findings["Network Packet Capture"] += @{
        Title = "Wireshark Not Found"
        Description = "Wireshark is not installed. Manual packet capture setup required."
        Status = "Warning"
    }
}

# Generate capture filters
$darktideProcess = Get-Process -Name "Darktide" -ErrorAction SilentlyContinue
$processFilter = if ($darktideProcess) {
    "process.id == $($darktideProcess.Id)"
} else {
    "process.name == `"Darktide.exe`""
}

$ipFilter = ($backendConfig.IPs | ForEach-Object { "ip.addr == $_" }) -join " or "
$combinedFilter = "($processFilter) and ($ipFilter) and tcp.port == 443"

Write-Log "Generated capture filter: $combinedFilter" -Level Info

$captureInstructions += "Wireshark Filter: $combinedFilter"
$captureInstructions += "Netsh Trace Command: netsh trace start provider=Microsoft-Windows-Schannel capture=yes tracefile=darktide_trace.etl"

$findings["Network Packet Capture"] += @{
    Title = "Capture Filters Generated"
    Description = "Filters generated for Darktide process and backend IPs. Filter: $combinedFilter"
    Status = "Success"
}

Write-Host ""

# ============================================================================
# 1.3 Event Log Analysis
# ============================================================================

Write-Host "1.3 Event Log Analysis" -ForegroundColor Green
Write-Host ""

$schannelEvents = Get-SchannelEvents -Hours 24

if ($schannelEvents.Count -gt 0) {
    Write-Log "Found $($schannelEvents.Count) schannel-related events in last 24 hours" -Level Info
    
    $errorEvents = $schannelEvents | Where-Object { $_.Level -like "*Error*" -or $_.Level -like "*Warning*" }
    if ($errorEvents.Count -gt 0) {
        Write-Log "Found $($errorEvents.Count) error/warning events" -Level Warning
        $findings["Event Log Analysis"] += @{
            Title = "Schannel Errors Found"
            Description = "Found $($errorEvents.Count) error/warning events in schannel logs"
            Status = "Warning"
        }
        
        # Show recent errors
        $errorEvents | Select-Object -First 5 | ForEach-Object {
            Write-Host "  [$($_.Time)] $($_.Level): $($_.Message.Substring(0, [Math]::Min(100, $_.Message.Length)))..." -ForegroundColor Yellow
        }
    } else {
        Write-Log "No error events found in schannel logs" -Level Success
        $findings["Event Log Analysis"] += @{
            Title = "No Schannel Errors"
            Description = "No error or warning events found in schannel logs"
            Status = "Success"
        }
    }
    
    # Export events to CSV
    $eventsCsvPath = Join-Path (Initialize-ReportsDirectory) "schannel_events_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"
    Export-EventLogToCSV -Events $schannelEvents -OutputPath $eventsCsvPath
} else {
    Write-Log "No schannel events found in last 24 hours" -Level Info
    $findings["Event Log Analysis"] += @{
        Title = "No Recent Events"
        Description = "No schannel events found in last 24 hours"
        Status = "Info"
    }
}

Write-Host ""

# ============================================================================
# 1.4 Process Network Comparison
# ============================================================================

Write-Host "1.4 Process Network Comparison" -ForegroundColor Green
Write-Host ""

# Get Darktide process network connections
$darktideProcess = Get-Process -Name "Darktide" -ErrorAction SilentlyContinue
if ($darktideProcess) {
    Write-Log "Darktide is running (PID: $($darktideProcess.Id))" -Level Info
    
    try {
        $darktideConnections = Get-NetTCPConnection -OwningProcess $darktideProcess.Id -ErrorAction SilentlyContinue
        if ($darktideConnections) {
            Write-Log "Found $($darktideConnections.Count) active TCP connections for Darktide" -Level Info
            $backendConnections = $darktideConnections | Where-Object { 
                $backendConfig.IPs -contains $_.RemoteAddress.IPAddressToString 
            }
            
            if ($backendConnections) {
                Write-Log "Found $($backendConnections.Count) connections to backend IPs" -Level Success
                $findings["Process Network Comparison"] += @{
                    Title = "Darktide Backend Connections"
                    Description = "Active connections to backend servers found"
                    Status = "Success"
                }
            } else {
                Write-Log "No active connections to backend IPs" -Level Warning
                $findings["Process Network Comparison"] += @{
                    Title = "No Backend Connections"
                    Description = "Darktide is running but has no connections to backend servers"
                    Status = "Warning"
                }
            }
        }
    } catch {
        Write-Log "Could not query Darktide network connections: $_" -Level Warning
    }
} else {
    Write-Log "Darktide is not currently running" -Level Warning
    $findings["Process Network Comparison"] += @{
        Title = "Darktide Not Running"
        Description = "Darktide.exe is not running. Start Darktide to perform network comparison."
        Status = "Warning"
    }
}

# Test PowerShell connectivity (working case)
Write-Log "Testing PowerShell connectivity to backend (baseline)" -Level Info
$psConnectivity = Test-BackendConnectivity
if ($psConnectivity.SSLConnectivity) {
    Write-Log "PowerShell can connect to backend (Status: $($psConnectivity.SSLStatus), Time: $($psConnectivity.SSLTime)ms)" -Level Success
    $findings["Process Network Comparison"] += @{
        Title = "PowerShell Connectivity (Baseline)"
        Description = "PowerShell successfully connects to backend (working case)"
        Status = "Success"
    }
} else {
    Write-Log "PowerShell cannot connect to backend: $($psConnectivity.SSLError)" -Level Error
    $findings["Process Network Comparison"] += @{
        Title = "PowerShell Connectivity Failed"
        Description = "PowerShell cannot connect: $($psConnectivity.SSLError)"
        Status = "Error"
    }
}

Write-Host ""

# ============================================================================
# 1.5 Network Connectivity Tests
# ============================================================================

Write-Host "1.5 Network Connectivity Tests" -ForegroundColor Green
Write-Host ""

# Test backend connectivity
Write-Log "Testing backend server connectivity" -Level Info
$backendTest = Test-BackendConnectivity

if ($backendTest.DNSResolution) {
    Write-Log "DNS resolution successful: $($backendTest.ResolvedIPs -join ', ')" -Level Success
    $findings["Network Connectivity"] += @{
        Title = "DNS Resolution"
        Description = "Successfully resolved backend hostname to: $($backendTest.ResolvedIPs -join ', ')"
        Status = "Success"
    }
} else {
    Write-Log "DNS resolution failed: $($backendTest.DNSError)" -Level Error
    $findings["Network Connectivity"] += @{
        Title = "DNS Resolution Failed"
        Description = "Could not resolve backend hostname: $($backendTest.DNSError)"
        Status = "Error"
    }
}

foreach ($ipTest in $backendTest.IPs) {
    if ($ipTest.Reachable) {
        Write-Log "Backend IP $($ipTest.IP):443 is reachable" -Level Success
    } else {
        Write-Log "Backend IP $($ipTest.IP):443 is NOT reachable" -Level Error
        $findings["Network Connectivity"] += @{
            Title = "Backend IP Unreachable"
            Description = "Cannot reach backend IP $($ipTest.IP) on port 443"
            Status = "Error"
        }
    }
}

if ($backendTest.SSLConnectivity) {
    Write-Log "SSL connectivity successful (Status: $($backendTest.SSLStatus), Time: $($backendTest.SSLTime)ms)" -Level Success
    $findings["Network Connectivity"] += @{
        Title = "SSL Connectivity"
        Description = "SSL connection to backend successful"
        Status = "Success"
    }
} else {
    Write-Log "SSL connectivity failed: $($backendTest.SSLError)" -Level Error
    $findings["Network Connectivity"] += @{
        Title = "SSL Connectivity Failed"
        Description = "SSL connection failed: $($backendTest.SSLError)"
        Status = "Error"
    }
}

# Test revocation server connectivity
Write-Log "Testing certificate revocation server connectivity" -Level Info
$revocationTest = Test-RevocationServerConnectivity

$reachableRevocation = ($revocationTest.Servers | Where-Object { $_.Reachable }).Count
$totalRevocation = $revocationTest.Servers.Count

Write-Log "Revocation servers: $reachableRevocation/$totalRevocation reachable" -Level Info

if ($reachableRevocation -eq 0) {
    Write-Log "WARNING: No revocation servers are reachable!" -Level Warning
    $findings["Network Connectivity"] += @{
        Title = "Revocation Servers Unreachable"
        Description = "None of the certificate revocation servers are reachable. This may cause certificate validation issues."
        Status = "Warning"
    }
} else {
    $findings["Network Connectivity"] += @{
        Title = "Revocation Server Connectivity"
        Description = "$reachableRevocation/$totalRevocation revocation servers are reachable"
        Status = if ($reachableRevocation -eq $totalRevocation) { "Success" } else { "Warning" }
    }
}

Write-Host ""

# ============================================================================
# 1.6 System Configuration Analysis
# ============================================================================

Write-Host "1.6 System Configuration Analysis" -ForegroundColor Green
Write-Host ""

# Check certificate revocation settings (read-only)
$statePath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\WinTrust\Trust Providers\Software Publishing\State"
$certState = Get-ItemProperty -Path $statePath -Name "State" -ErrorAction SilentlyContinue

if ($certState) {
    if ($certState.State -eq 0x23C00) {
        Write-Log "WARNING: Certificate revocation checking is DISABLED (0x23C00)" -Level Warning
        Write-Log "This is a security risk affecting ALL applications!" -Level Warning
        $findings["System Configuration"] += @{
            Title = "Certificate Revocation Disabled"
            Description = "Certificate revocation checking is disabled globally (security risk)"
            Status = "Warning"
        }
    } else {
        Write-Log "Certificate revocation checking is enabled (State: $($certState.State))" -Level Success
        $findings["System Configuration"] += @{
            Title = "Certificate Revocation Enabled"
            Description = "Certificate revocation checking is enabled (State: $($certState.State))"
            Status = "Success"
        }
    }
} else {
    Write-Log "Certificate revocation using default settings" -Level Info
    $findings["System Configuration"] += @{
        Title = "Certificate Revocation (Default)"
        Description = "Certificate revocation using default Windows settings"
        Status = "Info"
    }
}

# Check firewall rules
$firewallRules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*Darktide*" }
if ($firewallRules) {
    Write-Log "Found $($firewallRules.Count) firewall rules for Darktide" -Level Info
    $outboundRules = $firewallRules | Where-Object { $_.Direction -eq "Outbound" }
    $inboundRules = $firewallRules | Where-Object { $_.Direction -eq "Inbound" }
    
    $findings["System Configuration"] += @{
        Title = "Firewall Rules"
        Description = "Found $($firewallRules.Count) firewall rules ($($outboundRules.Count) outbound, $($inboundRules.Count) inbound)"
        Status = "Info"
    }
    
    # Check for overly broad rules
    $broadRules = $firewallRules | Where-Object { 
        $_.Profile -contains "Public" -or 
        ($_.DisplayName -notlike "*Restricted*" -and $_.DisplayName -notlike "*Backend*")
    }
    if ($broadRules) {
        Write-Log "WARNING: Found potentially overly broad firewall rules" -Level Warning
        $findings["System Configuration"] += @{
            Title = "Broad Firewall Rules"
            Description = "Some firewall rules may be too permissive (apply to Public networks or lack destination restrictions)"
            Status = "Warning"
        }
    }
} else {
    Write-Log "No firewall rules found for Darktide" -Level Info
    $findings["System Configuration"] += @{
        Title = "No Firewall Rules"
        Description = "No specific firewall rules found for Darktide"
        Status = "Info"
    }
}

# Check network adapter priority
$adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Sort-Object InterfaceMetric
$primaryAdapter = $adapters | Select-Object -First 1
if ($primaryAdapter) {
    Write-Log "Primary network adapter: $($primaryAdapter.Name) (Metric: $($primaryAdapter.InterfaceMetric))" -Level Info
    $findings["System Configuration"] += @{
        Title = "Network Adapter Priority"
        Description = "Primary adapter: $($primaryAdapter.Name) (Metric: $($primaryAdapter.InterfaceMetric))"
        Status = "Info"
    }
}

# Check VPN/TAP adapters
$tapAdapters = Get-NetAdapter | Where-Object { 
    $_.InterfaceDescription -like "*TAP*" -or $_.InterfaceDescription -like "*OpenVPN*" 
}
if ($tapAdapters) {
    $activeTAP = $tapAdapters | Where-Object { $_.Status -eq "Up" }
    if ($activeTAP) {
        Write-Log "WARNING: Active TAP adapter found: $($activeTAP.Name)" -Level Warning
        $findings["System Configuration"] += @{
            Title = "Active VPN/TAP Adapter"
            Description = "Active TAP adapter may interfere with SSL connections: $($activeTAP.Name)"
            Status = "Warning"
        }
    } else {
        Write-Log "TAP adapters present but not active" -Level Info
        $findings["System Configuration"] += @{
            Title = "VPN/TAP Adapters"
            Description = "TAP adapters found but not active"
            Status = "Info"
        }
    }
}

# Check proxy settings
$proxy = netsh winhttp show proxy
if ($proxy -like "*proxy*" -and $proxy -notlike "*Direct access*") {
    Write-Log "Proxy detected: $proxy" -Level Warning
    $findings["System Configuration"] += @{
        Title = "Proxy Configuration"
        Description = "Proxy is configured and may interfere with SSL connections"
        Status = "Warning"
    }
} else {
    Write-Log "No proxy configured" -Level Info
}

# Check for SSL interception software
$securityProcesses = Get-Process | Where-Object { 
    $_.ProcessName -like "*kaspersky*" -or 
    $_.ProcessName -like "*norton*" -or 
    $_.ProcessName -like "*mcafee*" -or 
    $_.ProcessName -like "*avast*" -or 
    $_.ProcessName -like "*avg*" -or
    $_.ProcessName -like "*bitdefender*" -or
    $_.ProcessName -like "*eset*"
} | Select-Object -First 5

if ($securityProcesses) {
    Write-Log "Security software detected that may intercept SSL" -Level Warning
    $securityList = ($securityProcesses | ForEach-Object { $_.ProcessName }) -join ", "
    $findings["System Configuration"] += @{
        Title = "SSL Interception Software"
        Description = "Security software detected that may intercept SSL: $securityList"
        Status = "Warning"
    }
} else {
    Write-Log "No obvious SSL interception software detected" -Level Success
}

Write-Host ""

# ============================================================================
# 1.7 Diagnostic Report Generation
# ============================================================================

Write-Host "1.7 Generating Diagnostic Report" -ForegroundColor Green
Write-Host ""

$reportPath = if ($OutputPath) {
    $OutputPath
} else {
    Get-ReportPath -Type "diagnostic"
}

New-DiagnosticReport -Findings $findings -OutputPath $reportPath

Write-Host ""
Write-Host "=== Diagnostic Phase Complete ===" -ForegroundColor Cyan
Write-Host "Report saved to: $reportPath" -ForegroundColor Green
Write-Host ""

# Summary
$totalFindings = ($findings.Values | Measure-Object).Count
$errorCount = ($findings.Values | Where-Object { $_.Status -eq "Error" }).Count
$warningCount = ($findings.Values | Where-Object { $_.Status -eq "Warning" }).Count

Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  Total findings: $totalFindings" -ForegroundColor White
Write-Host "  Errors: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
Write-Host "  Warnings: $warningCount" -ForegroundColor $(if ($warningCount -gt 0) { "Yellow" } else { "Green" })
Write-Host ""

if ($errorCount -gt 0 -or $warningCount -gt 0) {
    Write-Host "Review the diagnostic report for detailed findings and recommendations." -ForegroundColor Yellow
}

