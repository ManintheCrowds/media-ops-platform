# Cursor Network Path Analysis Script
# Analyzes network path, latency, and packet loss to Cursor endpoints

param(
    [string[]]$Endpoints = @("api.cursor.com"),
    [int]$PingCount = 10,
    [int]$TracerouteHops = 30,
    [string]$OutputFile = "cursor-path-analysis.json"
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

function Test-PingLatency {
    param(
        [string]$Target,
        [int]$Count = 10
    )
    
    $result = @{
        Target = $Target
        Success = $false
        PacketsSent = 0
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
            $reply = $ping.Send($Target, 1000)  # 1 second timeout
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
    param(
        [string]$Target,
        [int]$MaxHops = 30
    )
    
    $result = @{
        Target = $Target
        Hops = @()
        Success = $false
        Error = $null
    }
    
    try {
        # Use tracert command (Windows built-in)
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
            } elseif ($line -match '^\s*(\d+)\s+\*\s+\*\s+\*\s+(.+)$') {
                $hops += @{
                    Hop = [int]$matches[1]
                    Latency1 = $null
                    Latency2 = $null
                    Latency3 = $null
                    Host = $matches[2].Trim()
                    LatencyAvg = $null
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

function Test-HTTPLatency {
    param([string]$Url)
    
    $result = @{
        Url = $Url
        Success = $false
        StatusCode = $null
        Latency = $null
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

function Analyze-Path {
    param([string[]]$Endpoints)
    
    $analysis = @{
        AnalysisDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Endpoints = @()
    }
    
    foreach ($endpoint in $Endpoints) {
        Write-Host "`nAnalyzing: $endpoint"
        Write-Host "=" * 50
        
        $endpointAnalysis = @{
            Hostname = $endpoint
            DNS = $null
            Ping = $null
            Traceroute = $null
            HTTP = $null
        }
        
        # DNS Resolution
        Write-Host "Testing DNS resolution..."
        $endpointAnalysis.DNS = Test-DNSResolution -Hostname $endpoint
        if ($endpointAnalysis.DNS.Resolved) {
            Write-Host "  Resolved to: $($endpointAnalysis.DNS.IPs -join ', ')"
            Write-Host "  Resolution time: $($endpointAnalysis.DNS.ResolutionTime) ms"
        } else {
            Write-Host "  DNS resolution failed: $($endpointAnalysis.DNS.Error)"
        }
        
        # Ping Test
        if ($endpointAnalysis.DNS.Resolved) {
            $targetIP = $endpointAnalysis.DNS.IPs[0]
            Write-Host "`nTesting ping to $targetIP..."
            $endpointAnalysis.Ping = Test-PingLatency -Target $targetIP -Count $PingCount
            if ($endpointAnalysis.Ping.Success) {
                Write-Host "  Packets: $($endpointAnalysis.Ping.PacketsReceived)/$($endpointAnalysis.Ping.PacketsSent) received"
                Write-Host "  Packet loss: $($endpointAnalysis.Ping.PacketLossPercent)%"
                Write-Host "  Latency: Min=$($endpointAnalysis.Ping.LatencyMin)ms, Max=$($endpointAnalysis.Ping.LatencyMax)ms, Avg=$($endpointAnalysis.Ping.LatencyAvg)ms"
            } else {
                Write-Host "  Ping failed: $($endpointAnalysis.Ping.Error)"
            }
        }
        
        # Traceroute
        Write-Host "`nRunning traceroute..."
        $endpointAnalysis.Traceroute = Test-Traceroute -Target $endpoint -MaxHops $TracerouteHops
        if ($endpointAnalysis.Traceroute.Success) {
            Write-Host "  Hops: $($endpointAnalysis.Traceroute.Hops.Count)"
            $endpointAnalysis.Traceroute.Hops | ForEach-Object {
                Write-Host "    Hop $($_.Hop): $($_.Host) (avg: $($_.LatencyAvg)ms)"
            }
        } else {
            Write-Host "  Traceroute failed: $($endpointAnalysis.Traceroute.Error)"
        }
        
        # HTTP Test
        $httpsUrl = "https://$endpoint"
        Write-Host "`nTesting HTTP latency to $httpsUrl..."
        $endpointAnalysis.HTTP = Test-HTTPLatency -Url $httpsUrl
        if ($endpointAnalysis.HTTP.Success) {
            Write-Host "  Status: $($endpointAnalysis.HTTP.StatusCode)"
            Write-Host "  Latency: $($endpointAnalysis.HTTP.Latency) ms"
        } else {
            Write-Host "  HTTP test failed: $($endpointAnalysis.HTTP.Error)"
        }
        
        $analysis.Endpoints += $endpointAnalysis
    }
    
    return $analysis
}

function Export-Analysis {
    param(
        [hashtable]$Analysis,
        [string]$OutputFile
    )
    
    $json = $Analysis | ConvertTo-Json -Depth 10
    $json | Out-File -FilePath $OutputFile -Encoding UTF8
    
    Write-Host "`nAnalysis Results:"
    Write-Host "================="
    Write-Host "Results saved to: $OutputFile"
    
    # Generate markdown summary
    $mdFile = $OutputFile -replace '\.json$', '.md'
    $mdContent = @"
# Cursor Network Path Analysis

**Analysis Date**: $($Analysis.AnalysisDate)

## Summary

"@
    
    foreach ($ep in $Analysis.Endpoints) {
        $mdContent += @"

### $($ep.Hostname)

**DNS Resolution**: $(if ($ep.DNS.Resolved) { "✓ Resolved to $($ep.DNS.IPs -join ', ') in $($ep.DNS.ResolutionTime)ms" } else { "✗ Failed: $($ep.DNS.Error)" })

**Ping Test**: $(if ($ep.Ping.Success) { "✓ $($ep.Ping.PacketsReceived)/$($ep.Ping.PacketsSent) packets, $($ep.Ping.PacketLossPercent)% loss, Avg: $($ep.Ping.LatencyAvg)ms" } else { "✗ Failed: $($ep.Ping.Error)" })

**HTTP Latency**: $(if ($ep.HTTP.Success) { "✓ $($ep.HTTP.Latency)ms (Status: $($ep.HTTP.StatusCode))" } else { "✗ Failed: $($ep.HTTP.Error)" })

**Traceroute Hops**: $($ep.Traceroute.Hops.Count)

"@
    }
    
    $mdContent | Out-File -FilePath $mdFile -Encoding UTF8
    Write-Host "Markdown summary saved to: $mdFile"
}

# Main execution
try {
    $analysis = Analyze-Path -Endpoints $Endpoints
    Export-Analysis -Analysis $analysis -OutputFile $OutputFile
} catch {
    Write-Error "Path analysis failed: $_"
    exit 1
}
