# Cursor Health Report Script
# Generates regular health reports on Cursor connection status

param(
    [string]$MetricsDirectory = "cursor-metrics",
    [string]$QualityDirectory = "cursor-quality-metrics",
    [string]$OutputFile = "cursor-health-report.html",
    [int]$Days = 1  # Number of days to analyze
)

$ErrorActionPreference = "Stop"

function Get-HealthMetrics {
    param(
        [string]$MetricsDir,
        [int]$Days
    )
    
    $endDate = Get-Date
    $startDate = $endDate.AddDays(-$Days)
    
    $files = Get-ChildItem -Path $MetricsDir -Filter "*.json" -Recurse | 
        Where-Object { $_.LastWriteTime -ge $startDate -and $_.LastWriteTime -le $endDate
    
    $metrics = @{
        TotalSamples = 0
        AverageActiveConnections = 0
        MaxActiveConnections = 0
        MinActiveConnections = 0
        ConnectionStability = 0
        UptimePercent = 0
    }
    
    $activeConnections = @()
    $hasConnections = 0
    
    foreach ($file in $files) {
        try {
            $data = Get-Content $file.FullName -Raw | ConvertFrom-Json
            if ($data.Metrics) {
                $metrics.TotalSamples++
                $active = $data.Metrics.ActiveConnections
                $activeConnections += $active
                
                if ($active -gt 0) {
                    $hasConnections++
                }
            }
        } catch {
            # Skip invalid files
        }
    }
    
    if ($activeConnections.Count -gt 0) {
        $metrics.AverageActiveConnections = [math]::Round(($activeConnections | Measure-Object -Average).Average, 2)
        $metrics.MaxActiveConnections = ($activeConnections | Measure-Object -Maximum).Maximum
        $metrics.MinActiveConnections = ($activeConnections | Measure-Object -Minimum).Minimum
        
        if ($metrics.TotalSamples -gt 0) {
            $metrics.UptimePercent = [math]::Round(($hasConnections / $metrics.TotalSamples) * 100, 2)
        }
        
        # Calculate stability (coefficient of variation)
        $stdDev = [math]::Sqrt((($activeConnections | ForEach-Object { [math]::Pow($_ - $metrics.AverageActiveConnections, 2) } | Measure-Object -Sum).Sum) / $activeConnections.Count)
        if ($metrics.AverageActiveConnections -gt 0) {
            $metrics.ConnectionStability = [math]::Round((1 - ($stdDev / $metrics.AverageActiveConnections)) * 100, 2)
        }
    }
    
    return $metrics
}

function Get-QualityMetrics {
    param(
        [string]$QualityDir,
        [int]$Days
    )
    
    $endDate = Get-Date
    $startDate = $endDate.AddDays(-$Days)
    
    $files = Get-ChildItem -Path $QualityDir -Filter "*.json" -Recurse | 
        Where-Object { $_.LastWriteTime -ge $startDate -and $_.LastWriteTime -le $endDate }
    
    $quality = @{
        AverageLatency = 0
        AveragePacketLoss = 0
        AverageDNSResolution = 0
        AverageHTTPLatency = 0
        Samples = 0
    }
    
    $latencies = @()
    $packetLosses = @()
    $dnsTimes = @()
    $httpLatencies = @()
    
    foreach ($file in $files) {
        try {
            $data = Get-Content $file.FullName -Raw | ConvertFrom-Json
            foreach ($endpoint in $data.Endpoints.PSObject.Properties.Name) {
                $epData = $data.Endpoints.$endpoint
                
                if ($epData.PingResults) {
                    foreach ($ping in $epData.PingResults) {
                        if ($ping.Success -and $ping.LatencyAvg) {
                            $latencies += $ping.LatencyAvg
                            $packetLosses += $ping.PacketLossPercent
                            $quality.Samples++
                        }
                    }
                }
                
                if ($epData.DNSResults) {
                    foreach ($dns in $epData.DNSResults) {
                        if ($dns.Resolved -and $dns.ResolutionTime) {
                            $dnsTimes += $dns.ResolutionTime
                        }
                    }
                }
                
                if ($epData.HTTPResults) {
                    foreach ($http in $epData.HTTPResults) {
                        if ($http.Success -and $http.Latency) {
                            $httpLatencies += $http.Latency
                        }
                    }
                }
            }
        } catch {
            # Skip invalid files
        }
    }
    
    if ($latencies.Count -gt 0) {
        $quality.AverageLatency = [math]::Round(($latencies | Measure-Object -Average).Average, 2)
    }
    if ($packetLosses.Count -gt 0) {
        $quality.AveragePacketLoss = [math]::Round(($packetLosses | Measure-Object -Average).Average, 2)
    }
    if ($dnsTimes.Count -gt 0) {
        $quality.AverageDNSResolution = [math]::Round(($dnsTimes | Measure-Object -Average).Average, 2)
    }
    if ($httpLatencies.Count -gt 0) {
        $quality.AverageHTTPLatency = [math]::Round(($httpLatencies | Measure-Object -Average).Average, 2)
    }
    
    return $quality
}

function Generate-HealthReport {
    param(
        [hashtable]$HealthMetrics,
        [hashtable]$QualityMetrics,
        [string]$OutputFile,
        [int]$Days
    )
    
    $reportDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    $html = @"
<!DOCTYPE html>
<html>
<head>
    <title>Cursor Health Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        h2 { color: #666; border-bottom: 2px solid #ddd; padding-bottom: 5px; }
        .summary { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: white; border: 1px solid #ddd; border-radius: 5px; min-width: 150px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #333; }
        .metric-label { font-size: 12px; color: #666; margin-top: 5px; }
        .good { color: green; }
        .warning { color: orange; }
        .bad { color: red; }
        table { border-collapse: collapse; width: 100%; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Cursor Connection Health Report</h1>
    <p><strong>Report Date:</strong> $reportDate</p>
    <p><strong>Analysis Period:</strong> Last $Days day(s)</p>
    
    <div class="summary">
        <h2>Connection Overview</h2>
        <div class="metric">
            <div class="metric-value">$($HealthMetrics.AverageActiveConnections)</div>
            <div class="metric-label">Avg Active Connections</div>
        </div>
        <div class="metric">
            <div class="metric-value">$($HealthMetrics.UptimePercent)%</div>
            <div class="metric-label">Uptime</div>
        </div>
        <div class="metric">
            <div class="metric-value">$($HealthMetrics.ConnectionStability)%</div>
            <div class="metric-label">Stability</div>
        </div>
        <div class="metric">
            <div class="metric-value">$($HealthMetrics.TotalSamples)</div>
            <div class="metric-label">Samples</div>
        </div>
    </div>
    
    <div class="summary">
        <h2>Connection Quality</h2>
        <div class="metric">
            <div class="metric-value">$($QualityMetrics.AverageLatency)ms</div>
            <div class="metric-label">Avg Latency</div>
        </div>
        <div class="metric">
            <div class="metric-value">$($QualityMetrics.AveragePacketLoss)%</div>
            <div class="metric-label">Packet Loss</div>
        </div>
        <div class="metric">
            <div class="metric-value">$($QualityMetrics.AverageDNSResolution)ms</div>
            <div class="metric-label">DNS Resolution</div>
        </div>
        <div class="metric">
            <div class="metric-value">$($QualityMetrics.AverageHTTPLatency)ms</div>
            <div class="metric-label">HTTP Latency</div>
        </div>
    </div>
    
    <h2>Connection Statistics</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Value</th>
        </tr>
        <tr>
            <td>Average Active Connections</td>
            <td>$($HealthMetrics.AverageActiveConnections)</td>
        </tr>
        <tr>
            <td>Maximum Active Connections</td>
            <td>$($HealthMetrics.MaxActiveConnections)</td>
        </tr>
        <tr>
            <td>Minimum Active Connections</td>
            <td>$($HealthMetrics.MinActiveConnections)</td>
        </tr>
        <tr>
            <td>Connection Stability</td>
            <td>$($HealthMetrics.ConnectionStability)%</td>
        </tr>
        <tr>
            <td>Uptime Percentage</td>
            <td>$($HealthMetrics.UptimePercent)%</td>
        </tr>
        <tr>
            <td>Total Samples</td>
            <td>$($HealthMetrics.TotalSamples)</td>
        </tr>
    </table>
    
    <h2>Quality Metrics</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Value</th>
        </tr>
        <tr>
            <td>Average Latency</td>
            <td>$($QualityMetrics.AverageLatency) ms</td>
        </tr>
        <tr>
            <td>Average Packet Loss</td>
            <td>$($QualityMetrics.AveragePacketLoss) %</td>
        </tr>
        <tr>
            <td>Average DNS Resolution Time</td>
            <td>$($QualityMetrics.AverageDNSResolution) ms</td>
        </tr>
        <tr>
            <td>Average HTTP Latency</td>
            <td>$($QualityMetrics.AverageHTTPLatency) ms</td>
        </tr>
        <tr>
            <td>Quality Samples</td>
            <td>$($QualityMetrics.Samples)</td>
        </tr>
    </table>
</body>
</html>
"@
    
    $html | Out-File -FilePath $OutputFile -Encoding UTF8
    Write-Host "Health report saved to: $OutputFile"
}

function Generate-Report {
    Write-Host "Generating Cursor health report..."
    Write-Host "Analysis period: Last $Days day(s)"
    
    $healthMetrics = @{}
    $qualityMetrics = @{}
    
    if (Test-Path $MetricsDirectory) {
        Write-Host "Loading connection metrics..."
        $healthMetrics = Get-HealthMetrics -MetricsDir $MetricsDirectory -Days $Days
    } else {
        Write-Warning "Metrics directory not found: $MetricsDirectory"
    }
    
    if (Test-Path $QualityDirectory) {
        Write-Host "Loading quality metrics..."
        $qualityMetrics = Get-QualityMetrics -QualityDir $QualityDirectory -Days $Days
    } else {
        Write-Warning "Quality directory not found: $QualityDirectory"
    }
    
    Generate-HealthReport -HealthMetrics $healthMetrics -QualityMetrics $qualityMetrics -OutputFile $OutputFile -Days $Days
    
    # Export JSON
    $jsonFile = $OutputFile -replace '\.html$', '.json'
    $report = @{
        ReportDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        AnalysisPeriod = $Days
        HealthMetrics = $healthMetrics
        QualityMetrics = $qualityMetrics
    }
    $report | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonFile -Encoding UTF8
    Write-Host "JSON report saved to: $jsonFile"
}

# Main execution
try {
    Generate-Report
} catch {
    Write-Error "Health report generation failed: $_"
    exit 1
}
