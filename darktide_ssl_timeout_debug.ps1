# PURPOSE: Runtime monitoring script to debug SSL timeout issues
# DEPENDENCIES: Windows PowerShell, admin privileges for some checks
# MODIFICATION NOTES: Captures runtime evidence during Darktide connection attempt

param(
    [switch]$Verbose
)

$logPath = "d:\portfolio-harness\.cursor\debug.log"
$sessionId = "darktide-debug-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$runId = "run1"

# Helper function to write NDJSON log
function Write-DebugLog {
    param(
        [string]$hypothesisId,
        [string]$location,
        [string]$message,
        [hashtable]$data = @{}
    )
    
    $guid = (New-Guid).Guid -replace '-', ''
    $logEntry = @{
        id = "log_$(Get-Date -Format 'yyyyMMddHHmmss')_$guid"
        timestamp = [DateTimeOffset]::Now.ToUnixTimeMilliseconds()
        sessionId = $sessionId
        runId = $runId
        hypothesisId = $hypothesisId
        location = $location
        message = $message
        data = $data
    }
    
    $jsonLine = ($logEntry | ConvertTo-Json -Compress -Depth 10)
    Add-Content -Path $logPath -Value $jsonLine -Encoding UTF8
}

Write-Host "=== Darktide SSL Timeout Debug Monitor ===" -ForegroundColor Cyan
Write-Host "Session ID: $sessionId" -ForegroundColor Gray
Write-Host "Log file: $logPath" -ForegroundColor Gray
Write-Host ""
Write-Host "Starting monitoring... (Press Ctrl+C to stop)" -ForegroundColor Yellow
Write-Host ""

# Clear previous log
if (Test-Path $logPath) {
    Remove-Item $logPath -Force
    Write-Host "Cleared previous log file" -ForegroundColor Green
}

# ============================================================================
# HYPOTHESIS A: Firewall is blocking SSL handshake packets
# ============================================================================

Write-DebugLog -hypothesisId "A" -location "darktide_ssl_timeout_debug.ps1:start" -message "Starting firewall monitoring" -data @{
    hypothesis = "Firewall is blocking SSL handshake packets"
    checkType = "firewall_blocks"
}

# Monitor firewall blocks (requires admin)
$firewallBlocks = @()
$firewallMonitor = {
    $blocks = Get-WinEvent -FilterHashtable @{
        LogName = 'Microsoft-Windows-Windows Firewall With Advanced Security/Firewall'
        StartTime = (Get-Date).AddMinutes(-1)
    } -ErrorAction SilentlyContinue | Where-Object { $_.LevelDisplayName -eq 'Warning' -or $_.LevelDisplayName -eq 'Error' }
    
    foreach ($block in $blocks) {
        Write-DebugLog -hypothesisId "A" -location "firewall_monitor" -message "Firewall block detected" -data @{
            time = $block.TimeCreated
            level = $block.LevelDisplayName
            message = $block.Message
            id = $block.Id
        }
    }
}

# ============================================================================
# HYPOTHESIS B: Network adapter priority is wrong (traffic using wrong adapter)
# ============================================================================

Write-DebugLog -hypothesisId "B" -location "darktide_ssl_timeout_debug.ps1:start" -message "Starting network adapter monitoring" -data @{
    hypothesis = "Network adapter priority is wrong"
    checkType = "adapter_priority"
}

# Get network adapter priorities
$adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Sort-Object InterfaceMetric
$adapterInfo = $adapters | ForEach-Object {
    @{
        name = $_.Name
        interfaceDescription = $_.InterfaceDescription
        metric = $_.InterfaceMetric
        status = $_.Status
        linkSpeed = $_.LinkSpeed
    }
}

Write-DebugLog -hypothesisId "B" -location "adapter_check" -message "Network adapter priorities" -data @{
    adapters = $adapterInfo
    primaryAdapter = $adapterInfo[0]
}

# ============================================================================
# HYPOTHESIS C: VPN/TAP adapter is interfering with SSL traffic
# ============================================================================

Write-DebugLog -hypothesisId "C" -location "darktide_ssl_timeout_debug.ps1:start" -message "Starting VPN/TAP adapter check" -data @{
    hypothesis = "VPN/TAP adapter is interfering"
    checkType = "vpn_interference"
}

$tapAdapters = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like "*TAP*" -or $_.InterfaceDescription -like "*VPN*" }
$tapInfo = $tapAdapters | ForEach-Object {
    @{
        name = $_.Name
        interfaceDescription = $_.InterfaceDescription
        status = $_.Status
        metric = $_.InterfaceMetric
    }
}

Write-DebugLog -hypothesisId "C" -location "tap_check" -message "TAP/VPN adapters found" -data @{
    tapAdapters = $tapInfo
    count = $tapAdapters.Count
}

# ============================================================================
# HYPOTHESIS D: DNS resolution is slow/failing for backend servers
# ============================================================================

Write-DebugLog -hypothesisId "D" -location "darktide_ssl_timeout_debug.ps1:start" -message "Starting DNS resolution test" -data @{
    hypothesis = "DNS resolution is slow/failing"
    checkType = "dns_resolution"
}

$backendHosts = @(
    "bsp-sup-sd.atoma-discovery.com",
    "18.160.181.16",
    "18.160.181.108",
    "18.160.181.109",
    "18.160.181.111"
)

foreach ($host in $backendHosts) {
    $dnsStart = Get-Date
    try {
        if ($host -match '^\d+\.\d+\.\d+\.\d+$') {
            $result = $host
            $resolved = $true
        } else {
            $result = Resolve-DnsName -Name $host -ErrorAction Stop | Select-Object -First 1 -ExpandProperty IPAddress
            $resolved = $true
        }
        $dnsTime = ((Get-Date) - $dnsStart).TotalMilliseconds
        Write-DebugLog -hypothesisId "D" -location "dns_resolve" -message "DNS resolution successful" -data @{
            host = $host
            ip = $result
            timeMs = $dnsTime
            resolved = $resolved
        }
    } catch {
        $dnsTime = ((Get-Date) - $dnsStart).TotalMilliseconds
        Write-DebugLog -hypothesisId "D" -location "dns_resolve" -message "DNS resolution failed" -data @{
            host = $host
            error = $_.Exception.Message
            timeMs = $dnsTime
            resolved = $false
        }
    }
}

# ============================================================================
# HYPOTHESIS E: Windows schannel timeout settings are too short
# ============================================================================

Write-DebugLog -hypothesisId "E" -location "darktide_ssl_timeout_debug.ps1:start" -message "Checking schannel timeout settings" -data @{
    hypothesis = "Schannel timeout settings are too short"
    checkType = "schannel_timeout"
}

$schannelPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL"
$clientCacheTime = Get-ItemProperty -Path $schannelPath -Name "ClientCacheTime" -ErrorAction SilentlyContinue
$serverCacheTime = Get-ItemProperty -Path $schannelPath -Name "ServerCacheTime" -ErrorAction SilentlyContinue

Write-DebugLog -hypothesisId "E" -location "schannel_check" -message "Schannel timeout configuration" -data @{
    clientCacheTime = if ($clientCacheTime) { $clientCacheTime.ClientCacheTime } else { "default" }
    serverCacheTime = if ($serverCacheTime) { $serverCacheTime.ServerCacheTime } else { "default" }
}

# ============================================================================
# HYPOTHESIS F: Network congestion or packet loss causing timeouts
# ============================================================================

Write-DebugLog -hypothesisId "F" -location "darktide_ssl_timeout_debug.ps1:start" -message "Starting network connectivity test" -data @{
    hypothesis = "Network congestion or packet loss"
    checkType = "network_connectivity"
}

# Test connectivity to backend
foreach ($ip in @("18.160.181.16", "18.160.181.108", "18.160.181.109", "18.160.181.111")) {
    $testStart = Get-Date
    try {
        $test = Test-NetConnection -ComputerName $ip -Port 443 -WarningAction SilentlyContinue -InformationLevel Quiet
        $testTime = ((Get-Date) - $testStart).TotalMilliseconds
        Write-DebugLog -hypothesisId "F" -location "connectivity_test" -message "Connectivity test result" -data @{
            ip = $ip
            port = 443
            reachable = $test
            timeMs = $testTime
        }
    } catch {
        $testTime = ((Get-Date) - $testStart).TotalMilliseconds
        Write-DebugLog -hypothesisId "F" -location "connectivity_test" -message "Connectivity test failed" -data @{
            ip = $ip
            port = 443
            error = $_.Exception.Message
            timeMs = $testTime
        }
    }
}

# ============================================================================
# Continuous monitoring during connection attempt
# ============================================================================

Write-Host "Monitoring Darktide process and network activity..." -ForegroundColor Yellow
Write-Host "Please start Darktide and attempt to connect now." -ForegroundColor Cyan
Write-Host "Monitoring for 60 seconds (or press Ctrl+C to stop early)" -ForegroundColor Gray
Write-Host ""

$monitoringDuration = 60 # seconds
$startTime = Get-Date
$endTime = $startTime.AddSeconds($monitoringDuration)
$lastCheck = $startTime

while ((Get-Date) -lt $endTime) {
    try {
        $currentTime = Get-Date
        $elapsed = ($currentTime - $startTime).TotalSeconds
        
        # Check if Darktide is running
        $darktideProcess = Get-Process -Name "Darktide" -ErrorAction SilentlyContinue
        
        if ($darktideProcess) {
            Write-DebugLog -hypothesisId "ALL" -location "process_monitor" -message "Darktide process detected" -data @{
                pid = $darktideProcess.Id
                cpu = $darktideProcess.CPU
                memory = $darktideProcess.WorkingSet64
                elapsedSeconds = $elapsed
            }
            
            # Monitor network connections for Darktide
            $connections = Get-NetTCPConnection -OwningProcess $darktideProcess.Id -ErrorAction SilentlyContinue | Where-Object {
                $_.RemoteAddress -like "18.160.181.*" -or $_.RemotePort -eq 443
            }
            
            if ($connections) {
                foreach ($conn in $connections) {
                    Write-DebugLog -hypothesisId "F" -location "connection_monitor" -message "Active network connection" -data @{
                        localAddress = $conn.LocalAddress
                        localPort = $conn.LocalPort
                        remoteAddress = $conn.RemoteAddress
                        remotePort = $conn.RemotePort
                        state = $conn.State
                        owningProcess = $conn.OwningProcess
                        elapsedSeconds = $elapsed
                    }
                }
            } else {
                Write-DebugLog -hypothesisId "F" -location "connection_monitor" -message "No backend connections found" -data @{
                    elapsedSeconds = $elapsed
                }
            }
        }
        
        # Check for new schannel errors in Event Log
        try {
            $schannelErrors = Get-WinEvent -FilterHashtable @{
                LogName = 'System'
                ProviderName = 'Microsoft-Windows-Schannel'
                StartTime = $lastCheck
            } -ErrorAction SilentlyContinue -MaxEvents 10
            
            foreach ($error in $schannelErrors) {
                Write-DebugLog -hypothesisId "E" -location "schannel_event" -message "Schannel error detected" -data @{
                    time = $error.TimeCreated
                    level = $error.LevelDisplayName
                    id = $error.Id
                    message = $error.Message
                    elapsedSeconds = $elapsed
                }
            }
        } catch {
            # Schannel events may not be available, ignore
        }
        
        $lastCheck = $currentTime
        Start-Sleep -Seconds 2
        
    } catch {
        Write-DebugLog -hypothesisId "ALL" -location "monitor_error" -message "Monitoring error" -data @{
            error = $_.Exception.Message
            elapsedSeconds = $elapsed
        }
        Start-Sleep -Seconds 2
    }
}

Write-DebugLog -hypothesisId "ALL" -location "monitor_complete" -message "Monitoring period completed" -data @{
    durationSeconds = $monitoringDuration
    endTime = Get-Date
}

Write-Host ""
Write-Host "Monitoring complete. Check log file: $logPath" -ForegroundColor Green

