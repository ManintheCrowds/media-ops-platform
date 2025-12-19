# Cursor Connection Quality Monitor
# Monitors latency, packet loss, DNS resolution, and connection quality

param(
    [string[]]$Endpoints = @("api.cursor.com"),
    [int]$Interval = 30,  # Monitoring interval in seconds
    [int]$PingCount = 5,
    [string]$OutputDir = "cursor-quality-metrics",
    [switch]$ExportPrometheus
)

$ErrorActionPreference = "Stop"

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

function Test-DNSResolution {
    param([string]$Hostname)
    
    $result = @{
        Hostname = $Hostname
        Resolved = $false
        IPs = @()
        ResolutionTime = $null
        Error = $null
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
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

function Test-PingLatency {
    param(
        [string]$Target,
        [int]$Count = 5
    )
    
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
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
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

function Test-HTTPLatency {
    param([string]$Url)
    
    $result = @{
        Url = $Url
        Success = $false
        StatusCode = $null
        Latency = $null
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Error = $null
    }
    
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri $Url -Method Head -TimeoutSec 10 -UseBasicParsing
        $stopwatch.Stop()
        
        $result.Success = $true
        $result.StatusCode = $response.StatusCode
        $result.Latency = $stopwatch.ElapsedMilliseconds
    } catch {
        $result.Error = $_.Exception.Message
    }
    
    return $result
}

function Test-WebSocketConnection {
    param([string]$Url)
    
    $result = @{
        Url = $Url
        Success = $false
        ConnectionTime = $null
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Error = $null
    }
    
    # WebSocket testing requires additional libraries
    # This is a placeholder for future implementation
    $result.Error = "WebSocket testing requires additional implementation"
    
    return $result
}

function Monitor-Quality {
    $allMetrics = @{
        StartTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Endpoints = @{}
    }
    
    Write-Host "Starting connection quality monitoring..."
    Write-Host "Endpoints: $($Endpoints -join ', ')"
    Write-Host "Interval: $Interval seconds"
    
    while ($true) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Write-Host "`n[$timestamp] Running quality tests..."
        
        foreach ($endpoint in $Endpoints) {
            if (-not $allMetrics.Endpoints.ContainsKey($endpoint)) {
                $allMetrics.Endpoints[$endpoint] = @{
                    DNSResults = @()
                    PingResults = @()
                    HTTPResults = @()
                    WebSocketResults = @()
                }
            }
            
            # DNS Test
            Write-Host "  Testing DNS for $endpoint..."
            $dnsResult = Test-DNSResolution -Hostname $endpoint
            $allMetrics.Endpoints[$endpoint].DNSResults += $dnsResult
            if ($dnsResult.Resolved) {
                Write-Host "    DNS: $($dnsResult.ResolutionTime)ms -> $($dnsResult.IPs -join ', ')"
            } else {
                Write-Host "    DNS: Failed - $($dnsResult.Error)"
            }
            
            # Ping Test
            if ($dnsResult.Resolved) {
                $targetIP = $dnsResult.IPs[0]
                Write-Host "  Testing ping to $targetIP..."
                $pingResult = Test-PingLatency -Target $targetIP -Count $PingCount
                $allMetrics.Endpoints[$endpoint].PingResults += $pingResult
                if ($pingResult.Success) {
                    Write-Host "    Ping: $($pingResult.PacketsReceived)/$($pingResult.PacketsSent) packets, $($pingResult.PacketLossPercent)% loss, Avg: $($pingResult.LatencyAvg)ms"
                } else {
                    Write-Host "    Ping: Failed - $($pingResult.Error)"
                }
            }
            
            # HTTP Test
            $httpsUrl = "https://$endpoint"
            Write-Host "  Testing HTTP to $httpsUrl..."
            $httpResult = Test-HTTPLatency -Url $httpsUrl
            $allMetrics.Endpoints[$endpoint].HTTPResults += $httpResult
            if ($httpResult.Success) {
                Write-Host "    HTTP: $($httpResult.Latency)ms (Status: $($httpResult.StatusCode))"
            } else {
                Write-Host "    HTTP: Failed - $($httpResult.Error)"
            }
        }
        
        # Export metrics
        $jsonFile = Join-Path $OutputDir "cursor-quality-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
        $allMetrics | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonFile -Encoding UTF8
        
        if ($ExportPrometheus) {
            Export-PrometheusMetrics -Metrics $allMetrics
        }
        
        Start-Sleep -Seconds $Interval
    }
}

function Export-PrometheusMetrics {
    param([hashtable]$Metrics)
    
    $promFile = Join-Path $OutputDir "cursor-quality.prom"
    $promMetrics = @()
    
    foreach ($endpoint in $Metrics.Endpoints.Keys) {
        $epMetrics = $Metrics.Endpoints[$endpoint]
        
        # Latest DNS metrics
        if ($epMetrics.DNSResults.Count -gt 0) {
            $latestDNS = $epMetrics.DNSResults[-1]
            if ($latestDNS.Resolved) {
                $promMetrics += "cursor_dns_resolution_seconds{endpoint=`"$endpoint`"} $([math]::Round($latestDNS.ResolutionTime / 1000, 3))"
            }
        }
        
        # Latest ping metrics
        if ($epMetrics.PingResults.Count -gt 0) {
            $latestPing = $epMetrics.PingResults[-1]
            if ($latestPing.Success) {
                $promMetrics += "cursor_latency_seconds{endpoint=`"$endpoint`"} $([math]::Round($latestPing.LatencyAvg / 1000, 3))"
                $promMetrics += "cursor_packet_loss_ratio{endpoint=`"$endpoint`"} $([math]::Round($latestPing.PacketLossPercent / 100, 3))"
            }
        }
        
        # Latest HTTP metrics
        if ($epMetrics.HTTPResults.Count -gt 0) {
            $latestHTTP = $epMetrics.HTTPResults[-1]
            if ($latestHTTP.Success) {
                $promMetrics += "cursor_http_latency_seconds{endpoint=`"$endpoint`"} $([math]::Round($latestHTTP.Latency / 1000, 3))"
            }
        }
    }
    
    $promMetrics -join "`n" | Out-File -FilePath $promFile -Encoding UTF8 -NoNewline
}

# Main execution
try {
    Monitor-Quality
} catch {
    Write-Error "Quality monitoring failed: $_"
    exit 1
}
