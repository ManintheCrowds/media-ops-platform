# Cursor Endpoint Discovery Script
# Discovers all network endpoints that Cursor IDE connects to

param(
    [int]$Duration = 300,  # Duration in seconds to monitor
    [string]$OutputFile = "cursor-endpoints.json",
    [switch]$Continuous
)

$ErrorActionPreference = "Stop"

# Known Cursor process names
$CursorProcessNames = @("Cursor", "cursor")

function Get-CursorProcess {
    $processes = Get-Process | Where-Object { 
        $CursorProcessNames -contains $_.ProcessName 
    }
    return $processes
}

function Get-CursorConnections {
    param([int[]]$ProcessIds)
    
    if (-not $ProcessIds) {
        return @()
    }
    
    $connections = Get-NetTCPConnection -ErrorAction SilentlyContinue | 
        Where-Object { $ProcessIds -contains $_.OwningProcess } |
        Where-Object { $_.State -eq "Established" }
    
    return $connections
}

function Resolve-Endpoint {
    param(
        [string]$RemoteAddress,
        [int]$RemotePort
    )
    
    $result = @{
        IP = $RemoteAddress
        Port = $RemotePort
        Hostname = $null
        Resolved = $false
    }
    
    try {
        $hostname = [System.Net.Dns]::GetHostEntry($RemoteAddress).HostName
        $result.Hostname = $hostname
        $result.Resolved = $true
    } catch {
        # IP may not resolve to hostname
    }
    
    return $result
}

function Get-DNSQueries {
    param([int[]]$ProcessIds)
    
    # Note: DNS query capture requires elevated permissions or network monitoring tools
    # This is a placeholder for future implementation
    Write-Host "DNS query capture requires additional tools (e.g., Wireshark, Process Monitor)"
    return @()
}

function Discover-Endpoints {
    Write-Host "Starting Cursor endpoint discovery..."
    Write-Host "Monitoring for $Duration seconds..."
    
    $endpoints = @{}
    $startTime = Get-Date
    $endTime = $startTime.AddSeconds($Duration)
    
    while ((Get-Date) -lt $endTime -or $Continuous) {
        $processes = Get-CursorProcess
        
        if (-not $processes) {
            Write-Host "Cursor process not found. Waiting..."
            Start-Sleep -Seconds 5
            continue
        }
        
        $processIds = $processes | Select-Object -ExpandProperty Id
        Write-Host "Found Cursor processes: $($processIds -join ', ')"
        
        $connections = Get-CursorConnections -ProcessIds $processIds
        
        foreach ($conn in $connections) {
            $key = "$($conn.RemoteAddress):$($conn.RemotePort)"
            
            if (-not $endpoints.ContainsKey($key)) {
                Write-Host "Discovered endpoint: $key"
                $endpoint = Resolve-Endpoint -RemoteAddress $conn.RemoteAddress -RemotePort $conn.RemotePort
                
                $endpoints[$key] = @{
                    IP = $conn.RemoteAddress
                    Port = $conn.RemotePort
                    Hostname = $endpoint.Hostname
                    Protocol = "TCP"
                    FirstSeen = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                    LastSeen = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                    ConnectionCount = 1
                    States = @($conn.State)
                }
            } else {
                $endpoints[$key].LastSeen = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                $endpoints[$key].ConnectionCount++
                if ($endpoints[$key].States -notcontains $conn.State) {
                    $endpoints[$key].States += $conn.State
                }
            }
        }
        
        Start-Sleep -Seconds 2
    }
    
    return $endpoints
}

function Export-Results {
    param(
        [hashtable]$Endpoints,
        [string]$OutputFile
    )
    
    $output = @{
        DiscoveryDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Duration = $Duration
        EndpointCount = $Endpoints.Count
        Endpoints = @()
    }
    
    foreach ($key in $Endpoints.Keys) {
        $output.Endpoints += $Endpoints[$key]
    }
    
    $json = $output | ConvertTo-Json -Depth 10
    $json | Out-File -FilePath $OutputFile -Encoding UTF8
    
    Write-Host "`nDiscovery Results:"
    Write-Host "=================="
    Write-Host "Total endpoints discovered: $($Endpoints.Count)"
    Write-Host "Results saved to: $OutputFile"
    Write-Host "`nEndpoints:"
    
    foreach ($key in $Endpoints.Keys | Sort-Object) {
        $ep = $Endpoints[$key]
        $hostname = if ($ep.Hostname) { " ($($ep.Hostname))" } else { "" }
        Write-Host "  - $($ep.IP):$($ep.Port)$hostname"
    }
    
    # Generate markdown summary
    $mdFile = $OutputFile -replace '\.json$', '.md'
    $mdContent = @"
# Cursor Endpoint Discovery Results

**Discovery Date**: $($output.DiscoveryDate)
**Duration**: $Duration seconds
**Total Endpoints**: $($Endpoints.Count)

## Endpoints

| IP Address | Port | Hostname | Protocol | Connections | First Seen | Last Seen |
|------------|------|----------|----------|-------------|------------|-----------|
"@
    
    foreach ($key in $Endpoints.Keys | Sort-Object) {
        $ep = $Endpoints[$key]
        $hostname = if ($ep.Hostname) { $ep.Hostname } else { "N/A" }
        $mdContent += "`n| $($ep.IP) | $($ep.Port) | $hostname | $($ep.Protocol) | $($ep.ConnectionCount) | $($ep.FirstSeen) | $($ep.LastSeen) |"
    }
    
    $mdContent | Out-File -FilePath $mdFile -Encoding UTF8
    Write-Host "`nMarkdown summary saved to: $mdFile"
}

# Main execution
try {
    $endpoints = Discover-Endpoints
    Export-Results -Endpoints $endpoints -OutputFile $OutputFile
} catch {
    Write-Error "Discovery failed: $_"
    exit 1
}
