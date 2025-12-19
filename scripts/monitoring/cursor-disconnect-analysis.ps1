# Cursor Disconnect Analysis Tool
# Analyzes disconnect patterns and correlations

param(
    [string]$LogDirectory = "cursor-metrics",
    [string]$OutputFile = "cursor-disconnect-analysis.html",
    [datetime]$StartDate,
    [datetime]$EndDate
)

$ErrorActionPreference = "Stop"

if (-not $StartDate) {
    $StartDate = (Get-Date).AddDays(-7)
}
if (-not $EndDate) {
    $EndDate = Get-Date
}

function Get-MetricFiles {
    param(
        [string]$Directory,
        [datetime]$Start,
        [datetime]$End
    )
    
    $files = Get-ChildItem -Path $Directory -Filter "*.json" -Recurse | 
        Where-Object { $_.LastWriteTime -ge $Start -and $_.LastWriteTime -le $End }
    
    return $files
}

function Parse-MetricFile {
    param([string]$FilePath)
    
    try {
        $content = Get-Content $FilePath -Raw | ConvertFrom-Json
        return $content
    } catch {
        Write-Warning "Failed to parse $FilePath : $_"
        return $null
    }
}

function Detect-Disconnects {
    param([array]$Metrics)
    
    $disconnects = @()
    $previousActive = $null
    
    foreach ($metric in $Metrics | Sort-Object { [DateTime]::Parse($_.Timestamp) }) {
        $currentActive = $metric.Metrics.ActiveConnections
        
        if ($previousActive -ne $null -and $currentActive -lt $previousActive) {
            $disconnect = @{
                Timestamp = [DateTime]::Parse($metric.Timestamp)
                PreviousConnections = $previousActive
                CurrentConnections = $currentActive
                DisconnectCount = $previousActive - $currentActive
            }
            $disconnects += $disconnect
        }
        
        $previousActive = $currentActive
    }
    
    return $disconnects
}

function Analyze-Patterns {
    param([array]$Disconnects)
    
    $patterns = @{
        TotalDisconnects = $Disconnects.Count
        ByHour = @{}
        ByDayOfWeek = @{}
        AverageDisconnectSize = 0
        MaxDisconnectSize = 0
        TimeBetweenDisconnects = @()
    }
    
    if ($Disconnects.Count -eq 0) {
        return $patterns
    }
    
    # Analyze by hour
    foreach ($disconnect in $Disconnects) {
        $hour = $disconnect.Timestamp.Hour
        if (-not $patterns.ByHour.ContainsKey($hour)) {
            $patterns.ByHour[$hour] = 0
        }
        $patterns.ByHour[$hour]++
    }
    
    # Analyze by day of week
    foreach ($disconnect in $Disconnects) {
        $day = $disconnect.Timestamp.DayOfWeek
        if (-not $patterns.ByDayOfWeek.ContainsKey($day)) {
            $patterns.ByDayOfWeek[$day] = 0
        }
        $patterns.ByDayOfWeek[$day]++
    }
    
    # Calculate average disconnect size
    $totalDisconnectSize = ($Disconnects | Measure-Object -Property DisconnectCount -Sum).Sum
    $patterns.AverageDisconnectSize = [math]::Round($totalDisconnectSize / $Disconnects.Count, 2)
    $patterns.MaxDisconnectSize = ($Disconnects | Measure-Object -Property DisconnectCount -Maximum).Maximum
    
    # Calculate time between disconnects
    $sortedDisconnects = $Disconnects | Sort-Object { $_.Timestamp }
    for ($i = 1; $i -lt $sortedDisconnects.Count; $i++) {
        $timeDiff = ($sortedDisconnects[$i].Timestamp - $sortedDisconnects[$i-1].Timestamp).TotalMinutes
        $patterns.TimeBetweenDisconnects += $timeDiff
    }
    
    return $patterns
}

function Correlate-WithNetworkEvents {
    param(
        [array]$Disconnects,
        [string]$EventLogDirectory
    )
    
    $correlations = @()
    
    if (Test-Path $EventLogDirectory) {
        $eventFiles = Get-ChildItem -Path $EventLogDirectory -Filter "*.json" -Recurse
        
        foreach ($disconnect in $Disconnects) {
            $windowStart = $disconnect.Timestamp.AddMinutes(-5)
            $windowEnd = $disconnect.Timestamp.AddMinutes(5)
            
            $nearbyEvents = $eventFiles | ForEach-Object {
                $events = Parse-MetricFile -FilePath $_.FullName
                if ($events) {
                    $events | Where-Object {
                        $eventTime = [DateTime]::Parse($_.TimeCreated)
                        $eventTime -ge $windowStart -and $eventTime -le $windowEnd
                    }
                }
            }
            
            if ($nearbyEvents) {
                $correlations += @{
                    Disconnect = $disconnect
                    NearbyEvents = $nearbyEvents
                    EventCount = $nearbyEvents.Count
                }
            }
        }
    }
    
    return $correlations
}

function Generate-AnalysisReport {
    param(
        [array]$Disconnects,
        [hashtable]$Patterns,
        [array]$Correlations,
        [string]$OutputFile
    )
    
    $html = @"
<!DOCTYPE html>
<html>
<head>
    <title>Cursor Disconnect Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        h2 { color: #666; border-bottom: 2px solid #ddd; padding-bottom: 5px; }
        .summary { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
        table { border-collapse: collapse; width: 100%; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .disconnect { background: #fff3cd; padding: 10px; margin: 5px 0; border-left: 3px solid #ffc107; }
    </style>
</head>
<body>
    <h1>Cursor Disconnect Analysis Report</h1>
    <p><strong>Analysis Period:</strong> $($StartDate.ToString('yyyy-MM-dd')) to $($EndDate.ToString('yyyy-MM-dd'))</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Disconnects:</strong> $($Patterns.TotalDisconnects)</p>
        <p><strong>Average Disconnect Size:</strong> $($Patterns.AverageDisconnectSize) connections</p>
        <p><strong>Maximum Disconnect Size:</strong> $($Patterns.MaxDisconnectSize) connections</p>
    </div>
    
    <h2>Disconnects by Hour</h2>
    <table>
        <tr><th>Hour</th><th>Disconnect Count</th></tr>
"@
    
    foreach ($hour in $Patterns.ByHour.Keys | Sort-Object) {
        $html += "<tr><td>$hour:00</td><td>$($Patterns.ByHour[$hour])</td></tr>"
    }
    
    $html += @"
    </table>
    
    <h2>Disconnects by Day of Week</h2>
    <table>
        <tr><th>Day</th><th>Disconnect Count</th></tr>
"@
    
    foreach ($day in $Patterns.ByDayOfWeek.Keys | Sort-Object) {
        $html += "<tr><td>$day</td><td>$($Patterns.ByDayOfWeek[$day])</td></tr>"
    }
    
    $html += @"
    </table>
    
    <h2>Recent Disconnects</h2>
"@
    
    $recentDisconnects = $Disconnects | Sort-Object { $_.Timestamp } -Descending | Select-Object -First 20
    
    foreach ($disconnect in $recentDisconnects) {
        $html += @"
    <div class="disconnect">
        <p><strong>Time:</strong> $($disconnect.Timestamp.ToString('yyyy-MM-dd HH:mm:ss'))</p>
        <p><strong>Disconnect Size:</strong> $($disconnect.DisconnectCount) connections</p>
        <p><strong>Previous:</strong> $($disconnect.PreviousConnections) connections → <strong>Current:</strong> $($disconnect.CurrentConnections) connections</p>
    </div>
"@
    }
    
    if ($Correlations.Count -gt 0) {
        $html += @"
    <h2>Network Event Correlations</h2>
    <p>Found $($Correlations.Count) disconnects with nearby network events</p>
"@
    }
    
    $html += @"
</body>
</html>
"@
    
    $html | Out-File -FilePath $OutputFile -Encoding UTF8
    Write-Host "Analysis report saved to: $OutputFile"
}

function Analyze-Disconnects {
    Write-Host "Analyzing Cursor disconnects..."
    Write-Host "Period: $($StartDate.ToString('yyyy-MM-dd')) to $($EndDate.ToString('yyyy-MM-dd'))"
    
    if (-not (Test-Path $LogDirectory)) {
        Write-Error "Log directory not found: $LogDirectory"
        exit 1
    }
    
    # Get metric files
    Write-Host "Loading metric files..."
    $metricFiles = Get-MetricFiles -Directory $LogDirectory -Start $StartDate -End $EndDate
    Write-Host "Found $($metricFiles.Count) metric files"
    
    # Parse metrics
    $allMetrics = @()
    foreach ($file in $metricFiles) {
        $metric = Parse-MetricFile -FilePath $file.FullName
        if ($metric) {
            $allMetrics += $metric
        }
    }
    
    Write-Host "Loaded $($allMetrics.Count) metric records"
    
    # Detect disconnects
    Write-Host "Detecting disconnects..."
    $disconnects = Detect-Disconnects -Metrics $allMetrics
    Write-Host "Found $($disconnects.Count) disconnect events"
    
    # Analyze patterns
    Write-Host "Analyzing patterns..."
    $patterns = Analyze-Patterns -Disconnects $disconnects
    
    # Correlate with network events
    $eventLogDir = Join-Path $LogDirectory "cursor-event-logs"
    Write-Host "Correlating with network events..."
    $correlations = Correlate-WithNetworkEvents -Disconnects $disconnects -EventLogDirectory $eventLogDir
    
    # Generate report
    Write-Host "Generating analysis report..."
    Generate-AnalysisReport -Disconnects $disconnects -Patterns $patterns -Correlations $correlations -OutputFile $OutputFile
    
    # Export JSON
    $jsonFile = $OutputFile -replace '\.html$', '.json'
    $analysis = @{
        Period = @{
            Start = $StartDate.ToString('yyyy-MM-dd HH:mm:ss')
            End = $EndDate.ToString('yyyy-MM-dd HH:mm:ss')
        }
        Disconnects = $disconnects
        Patterns = $patterns
        Correlations = $correlations
    }
    $analysis | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonFile -Encoding UTF8
    Write-Host "JSON analysis saved to: $jsonFile"
}

# Main execution
try {
    Analyze-Disconnects
} catch {
    Write-Error "Disconnect analysis failed: $_"
    exit 1
}
