# Application Process Monitor Template
# Generic monitoring script for any Windows application
# Based on Cursor monitoring pattern

param(
    [Parameter(Mandatory=$true)]
    [string]$AppName,
    
    [Parameter(Mandatory=$true)]
    [string]$ProcessName,
    
    [int]$Interval = 5,
    [string]$OutputDir,
    [switch]$ExportPrometheus,
    [string]$PrometheusPort = 9101,
    [string[]]$AdditionalProcessNames = @()
)

$ErrorActionPreference = "Stop"

# Set default output directory if not provided
if (-not $OutputDir) {
    $OutputDir = "${AppName}-metrics"
}

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Write-Host "Created output directory: $OutputDir" -ForegroundColor Green
}

# Build process name list
$ProcessNames = @($ProcessName) + $AdditionalProcessNames

function Get-AppProcess {
    $processes = Get-Process | Where-Object { 
        $ProcessNames -contains $_.ProcessName 
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
    }
    
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
        [string]$OutputFile,
        [string]$AppName
    )
    
    $metricPrefix = $AppName.ToLower().Replace(" ", "_").Replace("-", "_")
    
    $prometheusMetrics = @"
# HELP ${metricPrefix}_connections_active Current number of active $AppName connections
# TYPE ${metricPrefix}_connections_active gauge
${metricPrefix}_connections_active $($Metrics.ActiveConnections)

# HELP ${metricPrefix}_connections_total Total number of $AppName connections
# TYPE ${metricPrefix}_connections_total gauge
${metricPrefix}_connections_total $($Metrics.TotalConnections)

# HELP ${metricPrefix}_process_count Number of $AppName processes
# TYPE ${metricPrefix}_process_count gauge
${metricPrefix}_process_count $($Metrics.ProcessCount)

# HELP ${metricPrefix}_cpu_usage_seconds Total CPU usage in seconds
# TYPE ${metricPrefix}_cpu_usage_seconds counter
${metricPrefix}_cpu_usage_seconds $($Metrics.CPUUsage)

# HELP ${metricPrefix}_memory_usage_bytes Memory usage in bytes
# TYPE ${metricPrefix}_memory_usage_bytes gauge
${metricPrefix}_memory_usage_bytes $($Metrics.MemoryUsage)

"@
    
    foreach ($state in $Metrics.ConnectionsByState.Keys) {
        $stateLabel = $state.ToLower()
        $prometheusMetrics += "${metricPrefix}_connections_by_state{state=`"$stateLabel`"} $($Metrics.ConnectionsByState[$state])`n"
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
        AppName = $AppName
        Metrics = $Metrics
    }
    
    $json = $output | ConvertTo-Json -Depth 10
    $json | Out-File -FilePath $OutputFile -Encoding UTF8
}

function Monitor-App {
    Write-Host "Starting $AppName process monitoring..." -ForegroundColor Cyan
    Write-Host "Process name(s): $($ProcessNames -join ', ')" -ForegroundColor Gray
    Write-Host "Interval: $Interval seconds" -ForegroundColor Gray
    Write-Host "Output directory: $OutputDir" -ForegroundColor Gray
    
    if ($ExportPrometheus) {
        Write-Host "Prometheus export enabled on port $PrometheusPort" -ForegroundColor Yellow
    }
    
    $metricsFile = Join-Path $OutputDir "${AppName}-metrics.prom"
    $jsonFile = Join-Path $OutputDir "${AppName}-metrics.json"
    
    while ($true) {
        $processes = Get-AppProcess
        
        if ($processes) {
            $processIds = $processes | Select-Object -ExpandProperty Id
            $metrics = Get-ConnectionMetrics -ProcessIds $processIds
            
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Write-Host "[$timestamp] $AppName - Active: $($metrics.ActiveConnections), Total: $($metrics.TotalConnections), Processes: $($metrics.ProcessCount)" -ForegroundColor Green
            
            if ($ExportPrometheus) {
                Export-PrometheusMetrics -Metrics $metrics -OutputFile $metricsFile -AppName $AppName
            }
            
            Export-JSONMetrics -Metrics $metrics -OutputFile $jsonFile
        } else {
            Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $AppName process not found" -ForegroundColor Yellow
        }
        
        Start-Sleep -Seconds $Interval
    }
}

# Main execution
try {
    Monitor-App
} catch {
    Write-Error "Monitoring failed: $_"
    exit 1
}
