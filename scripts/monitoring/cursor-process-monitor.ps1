# Cursor Process Monitor Script
# Monitors Cursor.exe network connections and exports metrics

param(
    [int]$Interval = 5,  # Monitoring interval in seconds
    [string]$OutputDir = "cursor-metrics",
    [switch]$ExportPrometheus,
    [string]$PrometheusPort = 9101
)

$ErrorActionPreference = "Stop"

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$CursorProcessNames = @("Cursor", "cursor")

function Get-CursorProcess {
    $processes = Get-Process | Where-Object { 
        $CursorProcessNames -contains $_.ProcessName 
    }
    return $processes
}

function Get-ConnectionMetrics {
    param([int[]]$ProcessIds)
    
    if (-not $ProcessIds) {
        return @{
            ActiveConnections = 0
            TotalConnections = 0
            BytesSent = 0
            BytesReceived = 0
            ConnectionsByState = @{}
            ConnectionsByEndpoint = @()
        }
    }
    
    $connections = Get-NetTCPConnection -ErrorAction SilentlyContinue | 
        Where-Object { $ProcessIds -contains $_.OwningProcess }
    
    $metrics = @{
        ActiveConnections = ($connections | Where-Object { $_.State -eq "Established" }).Count
        TotalConnections = $connections.Count
        BytesSent = 0
        BytesReceived = 0
        ConnectionsByState = @{}
        ConnectionsByEndpoint = @()
        ConnectionDurations = @()
    }
    
    $endpointGroups = $connections | Group-Object -Property @{Expression={"{0}:{1}" -f $_.RemoteAddress, $_.RemotePort}}
    
    foreach ($conn in $connections) {
        $state = $conn.State
        if (-not $metrics.ConnectionsByState.ContainsKey($state)) {
            $metrics.ConnectionsByState[$state] = 0
        }
        $metrics.ConnectionsByState[$state]++
        
        $endpoint = "{0}:{1}" -f $conn.RemoteAddress, $conn.RemotePort
        $metrics.ConnectionsByEndpoint += @{
            Endpoint = $endpoint
            State = $state
            LocalPort = $conn.LocalPort
            RemotePort = $conn.RemotePort
        }
    }
    
    # Get process resource usage
    $processes = Get-Process -Id $ProcessIds -ErrorAction SilentlyContinue
    $totalCPU = ($processes | Measure-Object -Property CPU -Sum).Sum
    $totalMemory = ($processes | Measure-Object -Property WorkingSet -Sum).Sum
    
    $metrics.ProcessCount = $processes.Count
    $metrics.CPUUsage = $totalCPU
    $metrics.MemoryUsage = $totalMemory
    
    return $metrics
}

function Export-PrometheusMetrics {
    param(
        [hashtable]$Metrics,
        [string]$OutputFile
    )
    
    $prometheusMetrics = @"
# HELP cursor_connections_active Current number of active Cursor connections
# TYPE cursor_connections_active gauge
cursor_connections_active $($Metrics.ActiveConnections)

# HELP cursor_connections_total Total number of Cursor connections
# TYPE cursor_connections_total gauge
cursor_connections_total $($Metrics.TotalConnections)

# HELP cursor_process_count Number of Cursor processes
# TYPE cursor_process_count gauge
cursor_process_count $($Metrics.ProcessCount)

# HELP cursor_cpu_usage_seconds Total CPU usage in seconds
# TYPE cursor_cpu_usage_seconds counter
cursor_cpu_usage_seconds $($Metrics.CPUUsage)

# HELP cursor_memory_usage_bytes Memory usage in bytes
# TYPE cursor_memory_usage_bytes gauge
cursor_memory_usage_bytes $($Metrics.MemoryUsage)

"@
    
    foreach ($state in $Metrics.ConnectionsByState.Keys) {
        $stateLabel = $state.ToLower()
        $prometheusMetrics += "cursor_connections_by_state{state=`"$stateLabel`"} $($Metrics.ConnectionsByState[$state])`n"
    }
    
    $prometheusMetrics | Out-File -FilePath $OutputFile -Encoding UTF8 -NoNewline
}

function Export-JSONMetrics {
    param(
        [hashtable]$Metrics,
        [string]$OutputFile
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $output = @{
        Timestamp = $timestamp
        Metrics = $Metrics
    }
    
    $json = $output | ConvertTo-Json -Depth 10
    $json | Out-File -FilePath $OutputFile -Encoding UTF8
}

function Start-PrometheusServer {
    param(
        [string]$MetricsFile,
        [int]$Port
    )
    
    $listener = New-Object System.Net.HttpListener
    $listener.Prefixes.Add("http://localhost:$Port/")
    $listener.Start()
    
    Write-Host "Prometheus metrics server started on port $Port"
    Write-Host "Metrics endpoint: http://localhost:$Port/metrics"
    
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response
        
        if ($request.Url.AbsolutePath -eq "/metrics") {
            $metrics = Get-Content $MetricsFile -Raw
            $buffer = [System.Text.Encoding]::UTF8.GetBytes($metrics)
            $response.ContentLength64 = $buffer.Length
            $response.ContentType = "text/plain; version=0.0.4"
            $response.StatusCode = 200
            $response.OutputStream.Write($buffer, 0, $buffer.Length)
        } else {
            $response.StatusCode = 404
        }
        
        $response.Close()
    }
}

function Monitor-Cursor {
    Write-Host "Starting Cursor process monitoring..."
    Write-Host "Interval: $Interval seconds"
    Write-Host "Output directory: $OutputDir"
    
    if ($ExportPrometheus) {
        Write-Host "Prometheus export enabled on port $PrometheusPort"
    }
    
    $metricsFile = Join-Path $OutputDir "cursor-metrics.prom"
    $jsonFile = Join-Path $OutputDir "cursor-metrics.json"
    
    while ($true) {
        $processes = Get-CursorProcess
        
        if ($processes) {
            $processIds = $processes | Select-Object -ExpandProperty Id
            $metrics = Get-ConnectionMetrics -ProcessIds $processIds
            
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Write-Host "[$timestamp] Active: $($metrics.ActiveConnections), Total: $($metrics.TotalConnections), Processes: $($metrics.ProcessCount)"
            
            if ($ExportPrometheus) {
                Export-PrometheusMetrics -Metrics $metrics -OutputFile $metricsFile
            }
            
            Export-JSONMetrics -Metrics $metrics -OutputFile $jsonFile
        } else {
            Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Cursor process not found"
        }
        
        Start-Sleep -Seconds $Interval
    }
}

# Main execution
try {
    if ($ExportPrometheus) {
        # Start Prometheus server in background job
        $job = Start-Job -ScriptBlock {
            param($MetricsFile, $Port)
            # Prometheus server logic would go here
            # For now, we'll just export to file
        } -ArgumentList $metricsFile, $PrometheusPort
        
        Monitor-Cursor
    } else {
        Monitor-Cursor
    }
} catch {
    Write-Error "Monitoring failed: $_"
    exit 1
}
