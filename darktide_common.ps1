# PURPOSE: Shared utilities and functions for Darktide diagnostic and fix workflow
# DEPENDENCIES: Windows PowerShell
# MODIFICATION NOTES: Common functions used across all Darktide workflow scripts

#region Darktide Path Detection

function Get-DarktidePath {
    <#
    .SYNOPSIS
    Finds Darktide.exe in standard installation locations.
    
    .DESCRIPTION
    Searches common Steam library paths for Darktide installation.
    
    .OUTPUTS
    String. Full path to Darktide.exe if found, $null otherwise.
    #>
    
    $darktidePaths = @(
        "D:\SteamLibrary\steamapps\common\Warhammer 40,000 DARKTIDE\binaries\Darktide.exe",
        "E:\SteamLibrary\steamapps\common\Warhammer 40,000 DARKTIDE\binaries\Darktide.exe",
        "C:\Program Files (x86)\Steam\steamapps\common\Warhammer 40,000 DARKTIDE\binaries\Darktide.exe",
        "$env:ProgramFiles\Steam\steamapps\common\Warhammer 40,000 DARKTIDE\binaries\Darktide.exe",
        "$env:ProgramFiles(x86)\Steam\steamapps\common\Warhammer 40,000 DARKTIDE\binaries\Darktide.exe"
    )
    
    foreach ($path in $darktidePaths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    # Try to find via Steam library folders
    $steamPaths = @(
        "$env:ProgramFiles\Steam\steamapps\libraryfolders.vdf",
        "$env:ProgramFiles(x86)\Steam\steamapps\libraryfolders.vdf"
    )
    
    foreach ($steamConfig in $steamPaths) {
        if (Test-Path $steamConfig) {
            $content = Get-Content $steamConfig -Raw -ErrorAction SilentlyContinue
            if ($content) {
                $matches = [regex]::Matches($content, '"path"\s+"([^"]+)"')
                foreach ($match in $matches) {
                    $libraryPath = $match.Groups[1].Value
                    $testPath = Join-Path $libraryPath "steamapps\common\Warhammer 40,000 DARKTIDE\binaries\Darktide.exe"
                    if (Test-Path $testPath) {
                        return $testPath
                    }
                }
            }
        }
    }
    
    return $null
}

#endregion

#region Admin Check Functions

function Test-Administrator {
    <#
    .SYNOPSIS
    Checks if current PowerShell session is running with Administrator privileges.
    
    .OUTPUTS
    Boolean. $true if running as Administrator, $false otherwise.
    #>
    
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Require-Administrator {
    <#
    .SYNOPSIS
    Requires Administrator privileges, exits if not present.
    
    .PARAMETER Operation
    Description of the operation requiring admin rights.
    #>
    
    param(
        [string]$Operation = "this operation"
    )
    
    if (-not (Test-Administrator)) {
        Write-Host "ERROR: Administrator privileges required for $Operation" -ForegroundColor Red
        Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
        exit 1
    }
}

#endregion

#region Logging Functions

function Write-Log {
    <#
    .SYNOPSIS
    Writes a log message with timestamp and level.
    
    .PARAMETER Message
    The log message to write.
    
    .PARAMETER Level
    Log level: Info, Warning, Error, Success
    #>
    
    param(
        [string]$Message,
        [ValidateSet("Info", "Warning", "Error", "Success")]
        [string]$Level = "Info"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "Error"   { "Red" }
        "Warning" { "Yellow" }
        "Success" { "Green" }
        default   { "White" }
    }
    
    $prefix = switch ($Level) {
        "Error"   { "[ERROR]" }
        "Warning" { "[WARN]" }
        "Success" { "[OK]" }
        default   { "[INFO]" }
    }
    
    Write-Host "$timestamp $prefix $Message" -ForegroundColor $color
}

function Save-LogFile {
    <#
    .SYNOPSIS
    Saves log entries to a file.
    
    .PARAMETER LogEntries
    Array of log entry objects.
    
    .PARAMETER FilePath
    Path to save the log file.
    #>
    
    param(
        [array]$LogEntries,
        [string]$FilePath
    )
    
    $logContent = $LogEntries | ForEach-Object {
        "$($_.Timestamp) [$($_.Level)] $($_.Message)"
    }
    
    $logContent | Out-File -FilePath $FilePath -Encoding UTF8
    Write-Log "Log saved to: $FilePath" -Level Success
}

#endregion

#region Report Generation Helpers

function New-DiagnosticReport {
    <#
    .SYNOPSIS
    Creates an HTML diagnostic report.
    
    .PARAMETER Findings
    Hashtable of diagnostic findings.
    
    .PARAMETER OutputPath
    Path to save the HTML report.
    #>
    
    param(
        [hashtable]$Findings,
        [string]$OutputPath
    )
    
    $html = @"
<!DOCTYPE html>
<html>
<head>
    <title>Darktide Diagnostic Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .section { margin: 20px 0; padding: 15px; background: #f9f9f9; border-left: 4px solid #4CAF50; }
        .finding { margin: 10px 0; padding: 10px; background: white; border-radius: 3px; }
        .success { border-left: 4px solid #4CAF50; }
        .warning { border-left: 4px solid #FF9800; }
        .error { border-left: 4px solid #F44336; }
        .info { border-left: 4px solid #2196F3; }
        .timestamp { color: #999; font-size: 0.9em; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #4CAF50; color: white; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Darktide Diagnostic Report</h1>
        <p class="timestamp">Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</p>
"@
    
    foreach ($section in $Findings.Keys) {
        $html += @"
        <div class="section">
            <h2>$section</h2>
"@
        
        foreach ($finding in $Findings[$section]) {
            $class = switch ($finding.Status) {
                "Success" { "success" }
                "Warning" { "warning" }
                "Error"   { "error" }
                default   { "info" }
            }
            
            $html += @"
            <div class="finding $class">
                <strong>$($finding.Title)</strong><br>
                $($finding.Description)
            </div>
"@
        }
        
        $html += "</div>"
    }
    
    $html += @"
    </div>
</body>
</html>
"@
    
    $html | Out-File -FilePath $OutputPath -Encoding UTF8
    Write-Log "Diagnostic report saved to: $OutputPath" -Level Success
}

function New-ValidationReport {
    <#
    .SYNOPSIS
    Creates an HTML validation report comparing before/after states.
    
    .PARAMETER BeforeState
    Hashtable of before-state values.
    
    .PARAMETER AfterState
    Hashtable of after-state values.
    
    .PARAMETER OutputPath
    Path to save the HTML report.
    #>
    
    param(
        [hashtable]$BeforeState,
        [hashtable]$AfterState,
        [string]$OutputPath
    )
    
    $html = @"
<!DOCTYPE html>
<html>
<head>
    <title>Darktide Validation Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #4CAF50; color: white; }
        .changed { background-color: #FFF9C4; }
        .unchanged { background-color: #E8F5E9; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Darktide Validation Report</h1>
        <p class="timestamp">Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</p>
        <table>
            <tr><th>Setting</th><th>Before</th><th>After</th><th>Status</th></tr>
"@
    
    $allKeys = ($BeforeState.Keys + $AfterState.Keys) | Select-Object -Unique
    
    foreach ($key in $allKeys) {
        $before = if ($BeforeState.ContainsKey($key)) { $BeforeState[$key] } else { "N/A" }
        $after = if ($AfterState.ContainsKey($key)) { $AfterState[$key] } else { "N/A" }
        $changed = $before -ne $after
        $class = if ($changed) { "changed" } else { "unchanged" }
        $status = if ($changed) { "Changed" } else { "Unchanged" }
        
        $html += @"
            <tr class="$class">
                <td>$key</td>
                <td>$before</td>
                <td>$after</td>
                <td>$status</td>
            </tr>
"@
    }
    
    $html += @"
        </table>
    </div>
</body>
</html>
"@
    
    $html | Out-File -FilePath $OutputPath -Encoding UTF8
    Write-Log "Validation report saved to: $OutputPath" -Level Success
}

#endregion

#region Network Test Functions

function Test-BackendConnectivity {
    <#
    .SYNOPSIS
    Tests connectivity to Darktide backend servers.
    
    .OUTPUTS
    Hashtable with connectivity test results.
    #>
    
    $backendIPs = @("18.160.181.16", "18.160.181.108", "18.160.181.109", "18.160.181.111")
    $backendHost = "bsp-sup-sd.atoma-discovery.com"
    $results = @{
        Host = $backendHost
        IPs = @()
        DNSResolution = $false
        SSLConnectivity = $false
    }
    
    # Test DNS resolution
    try {
        $dnsResult = Resolve-DnsName -Name $backendHost -ErrorAction Stop
        $results.DNSResolution = $true
        $results.ResolvedIPs = $dnsResult | Select-Object -ExpandProperty IPAddress
    } catch {
        $results.DNSResolution = $false
        $results.DNSError = $_.Exception.Message
    }
    
    # Test IP connectivity
    foreach ($ip in $backendIPs) {
        $test = Test-NetConnection -ComputerName $ip -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
        $results.IPs += @{
            IP = $ip
            Reachable = $test
        }
    }
    
    # Test SSL connectivity
    try {
        $testUrl = "https://$backendHost/bishop/steam_1361210_default"
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri $testUrl -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        $stopwatch.Stop()
        $results.SSLConnectivity = $true
        $results.SSLStatus = $response.StatusCode
        $results.SSLTime = $stopwatch.ElapsedMilliseconds
    } catch {
        $results.SSLConnectivity = $false
        $results.SSLError = $_.Exception.Message
    }
    
    return $results
}

function Test-RevocationServerConnectivity {
    <#
    .SYNOPSIS
    Tests connectivity to certificate revocation servers.
    
    .OUTPUTS
    Hashtable with revocation server test results.
    #>
    
    $ocspServers = @(
        "ocsp.digicert.com",
        "ocsp.verisign.com",
        "ocsp.globalsign.com"
    )
    
    $results = @{
        Servers = @()
    }
    
    foreach ($server in $ocspServers) {
        try {
            $test = Test-NetConnection -ComputerName $server -Port 80 -InformationLevel Quiet -WarningAction SilentlyContinue
            $results.Servers += @{
                Server = $server
                Reachable = $test
            }
        } catch {
            $results.Servers += @{
                Server = $server
                Reachable = $false
                Error = $_.Exception.Message
            }
        }
    }
    
    return $results
}

#endregion

#region Event Log Query Helpers

function Get-SchannelEvents {
    <#
    .SYNOPSIS
    Queries Windows Event Logs for schannel-related events.
    
    .PARAMETER Hours
    Number of hours to look back.
    
    .OUTPUTS
    Array of schannel event objects.
    #>
    
    param(
        [int]$Hours = 24
    )
    
    $startTime = (Get-Date).AddHours(-$Hours)
    $events = @()
    
    # Query schannel operational log
    try {
        $schannelEvents = Get-WinEvent -LogName "Microsoft-Windows-Schannel/Operational" -ErrorAction SilentlyContinue | 
            Where-Object { $_.TimeCreated -ge $startTime }
        
        foreach ($event in $schannelEvents) {
            $events += @{
                Time = $event.TimeCreated
                Level = $event.LevelDisplayName
                Id = $event.Id
                Message = $event.Message
                LogName = "Schannel/Operational"
            }
        }
    } catch {
        Write-Log "Could not query schannel operational log: $_" -Level Warning
    }
    
    # Query system log for network/SSL errors
    try {
        $systemEvents = Get-WinEvent -LogName "System" -ErrorAction SilentlyContinue |
            Where-Object { 
                $_.TimeCreated -ge $startTime -and 
                ($_.Id -eq 10016 -or $_.Message -like "*schannel*" -or $_.Message -like "*SSL*" -or $_.Message -like "*TLS*")
            }
        
        foreach ($event in $systemEvents) {
            $events += @{
                Time = $event.TimeCreated
                Level = $event.LevelDisplayName
                Id = $event.Id
                Message = $event.Message
                LogName = "System"
            }
        }
    } catch {
        Write-Log "Could not query system log: $_" -Level Warning
    }
    
    return $events
}

function Export-EventLogToCSV {
    <#
    .SYNOPSIS
    Exports event log entries to CSV.
    
    .PARAMETER Events
    Array of event objects.
    
    .PARAMETER OutputPath
    Path to save the CSV file.
    #>
    
    param(
        [array]$Events,
        [string]$OutputPath
    )
    
    $events | Select-Object Time, Level, Id, LogName, Message | 
        Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8
    
    Write-Log "Event log exported to: $OutputPath" -Level Success
}

#endregion

#region Report Directory Management

function Initialize-ReportsDirectory {
    <#
    .SYNOPSIS
    Creates and initializes the reports directory.
    
    .OUTPUTS
    String. Path to reports directory.
    #>
    
    $reportsDir = Join-Path $PSScriptRoot "darktide_reports"
    
    if (-not (Test-Path $reportsDir)) {
        New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null
        Write-Log "Created reports directory: $reportsDir" -Level Success
    }
    
    return $reportsDir
}

function Get-ReportPath {
    <#
    .SYNOPSIS
    Generates a timestamped report file path.
    
    .PARAMETER Type
    Report type: diagnostic, validation, changes
    
    .PARAMETER Extension
    File extension (default: html)
    #>
    
    param(
        [ValidateSet("diagnostic", "validation", "changes")]
        [string]$Type,
        [string]$Extension = "html"
    )
    
    $reportsDir = Initialize-ReportsDirectory
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $filename = "darktide_${Type}_${timestamp}.${Extension}"
    
    return Join-Path $reportsDir $filename
}

#endregion

#region Backend Configuration

function Get-BackendConfiguration {
    <#
    .SYNOPSIS
    Returns Darktide backend server configuration.
    
    .OUTPUTS
    Hashtable with backend configuration.
    #>
    
    return @{
        Host = "bsp-sup-sd.atoma-discovery.com"
        IPs = @("18.160.181.16", "18.160.181.108", "18.160.181.109", "18.160.181.111")
        IPRange = "18.160.181.0/24"
        Port = 443
        Protocol = "TCP"
        Endpoint = "/bishop/steam_1361210_default"
    }
}

#endregion

# Functions are available when script is dot-sourced
# No Export-ModuleMember needed (this is a script, not a module)

