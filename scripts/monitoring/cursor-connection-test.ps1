# Cursor Connection Test Script
# Comprehensive connection testing to Cursor endpoints

param(
    [string[]]$Endpoints = @("api.cursor.com"),
    [switch]$TestWebSocket,
    [string]$OutputFile = "cursor-connection-test-report.html"
)

$ErrorActionPreference = "Stop"

function Test-DNSResolution {
    param([string]$Hostname)
    
    $result = @{
        Hostname = $Hostname
        Resolved = $false
        IPs = @()
        ResolutionTime = $null
        Error = $null
    }
    
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $hostEntry = [System.Net.Dns]::GetHostEntry($Hostname)
        $stopwatch.Stop()
        
        $result.Resolved = $true
        $result.IPs = $hostEntry.AddressList | ForEach-Object { $_.ToString() }
        $result.ResolutionTime = $stopwatch.ElapsedMilliseconds
    } catch {
        $result.Error = $_.Exception.Message
    }
    
    return $result
}

function Test-HTTPConnectivity {
    param([string]$Url)
    
    $result = @{
        Url = $Url
        Success = $false
        StatusCode = $null
        Latency = $null
        Headers = @{}
        Error = $null
    }
    
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri $Url -Method Head -TimeoutSec 10 -UseBasicParsing
        $stopwatch.Stop()
        
        $result.Success = $true
        $result.StatusCode = $response.StatusCode
        $result.Latency = $stopwatch.ElapsedMilliseconds
        $result.Headers = $response.Headers
    } catch {
        $result.Error = $_.Exception.Message
    }
    
    return $result
}

function Test-WebSocketConnectivity {
    param([string]$Url)
    
    $result = @{
        Url = $Url
        Success = $false
        ConnectionTime = $null
        Error = $null
    }
    
    # WebSocket testing requires additional libraries (e.g., System.Net.WebSockets)
    # This is a placeholder implementation
    try {
        $wssUrl = $Url -replace '^https://', 'wss://' -replace '^http://', 'ws://'
        if (-not $wssUrl.StartsWith('wss://') -and -not $wssUrl.StartsWith('ws://')) {
            $wssUrl = "wss://$Url"
        }
        
        # Note: Full WebSocket implementation would require .NET WebSocket client
        $result.Error = "WebSocket testing requires .NET WebSocket client implementation"
    } catch {
        $result.Error = $_.Exception.Message
    }
    
    return $result
}

function Test-PingLatency {
    param([string]$Target, [int]$Count = 10)
    
    $result = @{
        Target = $Target
        Success = $false
        PacketsSent = $Count
        PacketsReceived = 0
        PacketsLost = 0
        PacketLossPercent = 0
        LatencyMin = $null
        LatencyMax = $null
        LatencyAvg = $null
        Latencies = @()
        Error = $null
    }
    
    try {
        $ping = New-Object System.Net.NetworkInformation.Ping
        $latencies = @()
        $received = 0
        
        for ($i = 0; $i -lt $Count; $i++) {
            $reply = $ping.Send($Target, 1000)
            $result.PacketsSent++
            
            if ($reply.Status -eq "Success") {
                $received++
                $latencies += $reply.RoundtripTime
            }
        }
        
        $result.Success = $received -gt 0
        $result.PacketsReceived = $received
        $result.PacketsLost = $Count - $received
        $result.PacketLossPercent = [math]::Round((($Count - $received) / $Count) * 100, 2)
        $result.Latencies = $latencies
        
        if ($latencies.Count -gt 0) {
            $result.LatencyMin = ($latencies | Measure-Object -Minimum).Minimum
            $result.LatencyMax = ($latencies | Measure-Object -Maximum).Maximum
            $result.LatencyAvg = [math]::Round(($latencies | Measure-Object -Average).Average, 2)
        }
    } catch {
        $result.Error = $_.Exception.Message
    }
    
    return $result
}

function Test-Traceroute {
    param([string]$Target, [int]$MaxHops = 30)
    
    $result = @{
        Target = $Target
        Hops = @()
        Success = $false
        Error = $null
    }
    
    try {
        $tracertOutput = tracert -h $MaxHops -w 1000 $Target 2>&1
        
        $hops = @()
        foreach ($line in $tracertOutput) {
            if ($line -match '^\s*(\d+)\s+(\d+)\s+ms\s+(\d+)\s+ms\s+(\d+)\s+ms\s+(.+)$') {
                $hops += @{
                    Hop = [int]$matches[1]
                    Latency1 = [int]$matches[2]
                    Latency2 = [int]$matches[3]
                    Latency3 = [int]$matches[4]
                    Host = $matches[5].Trim()
                    LatencyAvg = [math]::Round(($matches[2] + $matches[3] + $matches[4]) / 3, 2)
                }
            }
        }
        
        $result.Hops = $hops
        $result.Success = $hops.Count -gt 0
    } catch {
        $result.Error = $_.Exception.Message
    }
    
    return $result
}

function Generate-HTMLReport {
    param(
        [hashtable]$TestResults,
        [string]$OutputFile
    )
    
    $html = @"
<!DOCTYPE html>
<html>
<head>
    <title>Cursor Connection Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        h2 { color: #666; border-bottom: 2px solid #ddd; padding-bottom: 5px; }
        .success { color: green; }
        .failure { color: red; }
        .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .test { margin: 10px 0; padding: 10px; border-left: 3px solid #ccc; }
        .test.success { border-left-color: green; }
        .test.failure { border-left-color: red; }
        table { border-collapse: collapse; width: 100%; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Cursor Connection Test Report</h1>
    <p><strong>Test Date:</strong> $($TestResults.TestDate)</p>
    <p><strong>Total Endpoints Tested:</strong> $($TestResults.Endpoints.Count)</p>
    
"@
    
    foreach ($endpoint in $TestResults.Endpoints.Keys) {
        $epResults = $TestResults.Endpoints[$endpoint]
        $html += "<div class='endpoint'><h2>Endpoint: $endpoint</h2>"
        
        # DNS Test
        $dnsClass = if ($epResults.DNS.Resolved) { "success" } else { "failure" }
        $html += "<div class='test $dnsClass'><h3>DNS Resolution</h3>"
        if ($epResults.DNS.Resolved) {
            $html += "<p>✓ Resolved to: $($epResults.DNS.IPs -join ', ')</p>"
            $html += "<p>Resolution time: $($epResults.DNS.ResolutionTime) ms</p>"
        } else {
            $html += "<p>✗ Failed: $($epResults.DNS.Error)</p>"
        }
        $html += "</div>"
        
        # Ping Test
        if ($epResults.DNS.Resolved) {
            $pingClass = if ($epResults.Ping.Success) { "success" } else { "failure" }
            $html += "<div class='test $pingClass'><h3>Ping Test</h3>"
            if ($epResults.Ping.Success) {
                $html += "<p>✓ Packets: $($epResults.Ping.PacketsReceived)/$($epResults.Ping.PacketsSent)</p>"
                $html += "<p>Packet loss: $($epResults.Ping.PacketLossPercent)%</p>"
                $html += "<p>Latency: Min=$($epResults.Ping.LatencyMin)ms, Max=$($epResults.Ping.LatencyMax)ms, Avg=$($epResults.Ping.LatencyAvg)ms</p>"
            } else {
                $html += "<p>✗ Failed: $($epResults.Ping.Error)</p>"
            }
            $html += "</div>"
        }
        
        # HTTP Test
        $httpClass = if ($epResults.HTTP.Success) { "success" } else { "failure" }
        $html += "<div class='test $httpClass'><h3>HTTP Connectivity</h3>"
        if ($epResults.HTTP.Success) {
            $html += "<p>✓ Status: $($epResults.HTTP.StatusCode)</p>"
            $html += "<p>Latency: $($epResults.HTTP.Latency) ms</p>"
        } else {
            $html += "<p>✗ Failed: $($epResults.HTTP.Error)</p>"
        }
        $html += "</div>"
        
        # WebSocket Test
        if ($TestWebSocket -and $epResults.WebSocket) {
            $wsClass = if ($epResults.WebSocket.Success) { "success" } else { "failure" }
            $html += "<div class='test $wsClass'><h3>WebSocket Connectivity</h3>"
            if ($epResults.WebSocket.Success) {
                $html += "<p>✓ Connected in $($epResults.WebSocket.ConnectionTime) ms</p>"
            } else {
                $html += "<p>✗ Failed: $($epResults.WebSocket.Error)</p>"
            }
            $html += "</div>"
        }
        
        # Traceroute
        if ($epResults.Traceroute.Success) {
            $html += "<div class='test'><h3>Traceroute</h3>"
            $html += "<table><tr><th>Hop</th><th>Host</th><th>Avg Latency (ms)</th></tr>"
            foreach ($hop in $epResults.Traceroute.Hops) {
                $html += "<tr><td>$($hop.Hop)</td><td>$($hop.Host)</td><td>$($hop.LatencyAvg)</td></tr>"
            }
            $html += "</table></div>"
        }
        
        $html += "</div>"
    }
    
    $html += @"
</body>
</html>
"@
    
    $html | Out-File -FilePath $OutputFile -Encoding UTF8
    Write-Host "Report saved to: $OutputFile"
}

function Run-ConnectionTests {
    Write-Host "Starting Cursor connection tests..."
    Write-Host "Endpoints: $($Endpoints -join ', ')"
    
    $testResults = @{
        TestDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Endpoints = @{}
    }
    
    foreach ($endpoint in $Endpoints) {
        Write-Host "`nTesting: $endpoint"
        Write-Host "=" * 50
        
        $epResults = @{
            DNS = $null
            Ping = $null
            HTTP = $null
            WebSocket = $null
            Traceroute = $null
        }
        
        # DNS Test
        Write-Host "Testing DNS resolution..."
        $epResults.DNS = Test-DNSResolution -Hostname $endpoint
        
        # Ping Test
        if ($epResults.DNS.Resolved) {
            $targetIP = $epResults.DNS.IPs[0]
            Write-Host "Testing ping to $targetIP..."
            $epResults.Ping = Test-PingLatency -Target $targetIP
        }
        
        # HTTP Test
        $httpsUrl = "https://$endpoint"
        Write-Host "Testing HTTP connectivity to $httpsUrl..."
        $epResults.HTTP = Test-HTTPConnectivity -Url $httpsUrl
        
        # WebSocket Test
        if ($TestWebSocket) {
            Write-Host "Testing WebSocket connectivity..."
            $epResults.WebSocket = Test-WebSocketConnectivity -Url $endpoint
        }
        
        # Traceroute
        Write-Host "Running traceroute..."
        $epResults.Traceroute = Test-Traceroute -Target $endpoint
        
        $testResults.Endpoints[$endpoint] = $epResults
    }
    
    # Generate report
    Generate-HTMLReport -TestResults $testResults -OutputFile $OutputFile
    
    # Also export JSON
    $jsonFile = $OutputFile -replace '\.html$', '.json'
    $testResults | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonFile -Encoding UTF8
    Write-Host "JSON results saved to: $jsonFile"
    
    return $testResults
}

# Main execution
try {
    $results = Run-ConnectionTests
    Write-Host "`nConnection tests completed!"
} catch {
    Write-Error "Connection test failed: $_"
    exit 1
}
