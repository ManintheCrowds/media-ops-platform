# PURPOSE: Phase 3 - Post-fix validation for Darktide SSL timeout fixes
# DEPENDENCIES: darktide_common.ps1, Windows PowerShell
# MODIFICATION NOTES: Validates fixes and monitors for side effects

param(
    [switch]$Verbose,
    [string]$BeforeStatePath,
    [string]$OutputPath
)

# Import common utilities
$commonPath = Join-Path $PSScriptRoot "darktide_common.ps1"
if (Test-Path $commonPath) {
    . $commonPath
} else {
    Write-Host "ERROR: darktide_common.ps1 not found!" -ForegroundColor Red
    exit 1
}

Write-Host "=== Darktide Validation Phase 3 ===" -ForegroundColor Cyan
Write-Host ""

$darktidePath = Get-DarktidePath
if (-not $darktidePath) {
    Write-Log "Darktide.exe not found" -Level Error
    exit 1
}

$beforeState = @{}
$afterState = @{}
$validationResults = @{
    "Connectivity" = @()
    "Darktide Specific" = @()
    "Side Effects" = @()
}

# Load before state if provided
if ($BeforeStatePath -and (Test-Path $BeforeStatePath)) {
    try {
        $beforeStateObj = Get-Content $BeforeStatePath | ConvertFrom-Json
        $beforeState = @{}
        $beforeStateObj.PSObject.Properties | ForEach-Object { $beforeState[$_.Name] = $_.Value }
        Write-Log "Loaded before state from: $BeforeStatePath" -Level Success
    } catch {
        Write-Log "Could not load before state: $_" -Level Warning
    }
}

# ============================================================================
# 3.1 Connectivity Validation
# ============================================================================

Write-Host "3.1 Connectivity Validation" -ForegroundColor Green
Write-Host ""

# Test backend connectivity from PowerShell (baseline)
Write-Log "Testing PowerShell connectivity to backend (baseline)..." -Level Info
$backendTest = Test-BackendConnectivity

if ($backendTest.SSLConnectivity) {
    Write-Log "PowerShell connectivity: SUCCESS (Status: $($backendTest.SSLStatus), Time: $($backendTest.SSLTime)ms)" -Level Success
    $validationResults["Connectivity"] += @{
        Title = "PowerShell Backend Connectivity"
        Description = "PowerShell successfully connects to backend (baseline working)"
        Status = "Success"
    }
    $afterState["PowerShellBackendConnectivity"] = "Success"
} else {
    Write-Log "PowerShell connectivity: FAILED - $($backendTest.SSLError)" -Level Error
    $validationResults["Connectivity"] += @{
        Title = "PowerShell Backend Connectivity"
        Description = "PowerShell cannot connect: $($backendTest.SSLError)"
        Status = "Error"
    }
    $afterState["PowerShellBackendConnectivity"] = "Failed"
}

# Verify firewall rules
Write-Log "Verifying firewall rules..." -Level Info
$firewallRules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*Darktide*" }
$outboundRules = $firewallRules | Where-Object { $_.Direction -eq "Outbound" -and $_.Enabled -eq $true }
$restrictedRules = $outboundRules | Where-Object { $_.DisplayName -like "*Restricted*" -or $_.DisplayName -like "*Backend*" }

if ($restrictedRules) {
    Write-Log "Found $($restrictedRules.Count) restricted firewall rules" -Level Success
    $validationResults["Connectivity"] += @{
        Title = "Firewall Rules"
        Description = "Restricted firewall rules are active and correct"
        Status = "Success"
    }
    $afterState["FirewallRules"] = "Restricted rules active"
} elseif ($outboundRules) {
    Write-Log "Found outbound rules but may not be restricted" -Level Warning
    $validationResults["Connectivity"] += @{
        Title = "Firewall Rules"
        Description = "Outbound rules exist but may be too permissive"
        Status = "Warning"
    }
    $afterState["FirewallRules"] = "Non-restricted rules"
} else {
    Write-Log "No outbound firewall rules found" -Level Warning
    $validationResults["Connectivity"] += @{
        Title = "Firewall Rules"
        Description = "No outbound firewall rules found for Darktide"
        Status = "Warning"
    }
    $afterState["FirewallRules"] = "No rules"
}

# Verify network adapter configuration
$adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Sort-Object InterfaceMetric
$primaryAdapter = $adapters | Select-Object -First 1
if ($primaryAdapter) {
    Write-Log "Primary adapter: $($primaryAdapter.Name) (Metric: $($primaryAdapter.InterfaceMetric))" -Level Info
    $afterState["PrimaryAdapter"] = "$($primaryAdapter.Name) (Metric: $($primaryAdapter.InterfaceMetric))"
}

Write-Host ""

# ============================================================================
# 3.2 Darktide-Specific Validation
# ============================================================================

Write-Host "3.2 Darktide-Specific Validation" -ForegroundColor Green
Write-Host ""

$darktideProcess = Get-Process -Name "Darktide" -ErrorAction SilentlyContinue

if ($darktideProcess) {
    Write-Log "Darktide is running (PID: $($darktideProcess.Id))" -Level Success
    $afterState["DarktideRunning"] = "Yes (PID: $($darktideProcess.Id))"
    
    # Monitor network connections
    Write-Log "Monitoring Darktide network connections..." -Level Info
    Start-Sleep -Seconds 2  # Give it a moment to establish connections
    
    try {
        $darktideConnections = Get-NetTCPConnection -OwningProcess $darktideProcess.Id -ErrorAction SilentlyContinue
        $backendConfig = Get-BackendConfiguration
        $backendConnections = $darktideConnections | Where-Object { 
            $backendConfig.IPs -contains $_.RemoteAddress.IPAddressToString -and $_.State -eq "Established"
        }
        
        if ($backendConnections) {
            Write-Log "Found $($backendConnections.Count) established connections to backend" -Level Success
            $validationResults["Darktide Specific"] += @{
                Title = "Backend Connections"
                Description = "Darktide has $($backendConnections.Count) established connections to backend servers"
                Status = "Success"
            }
            $afterState["DarktideBackendConnections"] = $backendConnections.Count
        } else {
            Write-Log "No established connections to backend servers" -Level Warning
            $validationResults["Darktide Specific"] += @{
                Title = "Backend Connections"
                Description = "Darktide is running but has no connections to backend servers"
                Status = "Warning"
            }
            $afterState["DarktideBackendConnections"] = 0
        }
    } catch {
        Write-Log "Could not query Darktide connections: $_" -Level Warning
    }
    
    # Check Event Viewer for new schannel errors
    Write-Log "Checking for new schannel errors..." -Level Info
    $recentEvents = Get-SchannelEvents -Hours 1
    $newErrors = $recentEvents | Where-Object { $_.Level -like "*Error*" }
    
    if ($newErrors.Count -gt 0) {
        Write-Log "Found $($newErrors.Count) new schannel errors in last hour" -Level Warning
        $validationResults["Darktide Specific"] += @{
            Title = "Schannel Errors"
            Description = "Found $($newErrors.Count) new schannel errors after fixes"
            Status = "Warning"
        }
        $afterState["NewSchannelErrors"] = $newErrors.Count
    } else {
        Write-Log "No new schannel errors found" -Level Success
        $validationResults["Darktide Specific"] += @{
            Title = "Schannel Errors"
            Description = "No new schannel errors detected"
            Status = "Success"
        }
        $afterState["NewSchannelErrors"] = 0
    }
} else {
    Write-Log "Darktide is not running" -Level Warning
    Write-Log "Please start Darktide to complete validation" -Level Info
    $validationResults["Darktide Specific"] += @{
        Title = "Darktide Not Running"
        Description = "Darktide.exe is not running. Start Darktide to complete validation."
        Status = "Warning"
    }
    $afterState["DarktideRunning"] = "No"
    $afterState["DarktideBackendConnections"] = "N/A"
    $afterState["NewSchannelErrors"] = "N/A"
}

Write-Host ""

# ============================================================================
# 3.3 Authentication Flow Test
# ============================================================================

Write-Host "3.3 Authentication Flow Test" -ForegroundColor Green
Write-Host ""

if ($darktideProcess) {
    Write-Log "Darktide is running - monitoring authentication flow..." -Level Info
    Write-Log "Please attempt to log in to Darktide now..." -Level Info
    Write-Host ""
    Write-Host "Waiting 30 seconds for login attempt..." -ForegroundColor Yellow
    Write-Host "Monitor the console for any timeout errors..." -ForegroundColor Yellow
    Write-Host ""
    
    # Monitor for 30 seconds
    $monitorStart = Get-Date
    $timeoutErrors = @()
    
    while (((Get-Date) - $monitorStart).TotalSeconds -lt 30) {
        Start-Sleep -Seconds 5
        
        # Check for new errors in event logs
        $recentErrors = Get-SchannelEvents -Hours 0.1  # Last 6 minutes
        $timeoutErrors = $recentErrors | Where-Object { 
            $_.Message -like "*timeout*" -or $_.Message -like "*timed out*" 
        }
        
        if ($timeoutErrors.Count -gt 0) {
            Write-Log "Timeout error detected!" -Level Error
            break
        }
        
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host ""
    
    if ($timeoutErrors.Count -gt 0) {
        Write-Log "AUTHENTICATION TEST: FAILED - Timeout errors detected" -Level Error
        $validationResults["Darktide Specific"] += @{
            Title = "Authentication Flow"
            Description = "Timeout errors detected during authentication attempt"
            Status = "Error"
        }
        $afterState["AuthenticationTest"] = "Failed - Timeout errors"
    } else {
        Write-Log "AUTHENTICATION TEST: No timeout errors detected" -Level Success
        Write-Log "If login was successful, validation passed!" -Level Success
        $validationResults["Darktide Specific"] += @{
            Title = "Authentication Flow"
            Description = "No timeout errors detected during authentication attempt"
            Status = "Success"
        }
        $afterState["AuthenticationTest"] = "No timeout errors"
    }
} else {
    Write-Log "Skipping authentication test - Darktide not running" -Level Warning
    $validationResults["Darktide Specific"] += @{
        Title = "Authentication Flow"
        Description = "Skipped - Darktide not running"
        Status = "Warning"
    }
    $afterState["AuthenticationTest"] = "Skipped"
}

Write-Host ""

# ============================================================================
# 3.4 Side Effect Monitoring
# ============================================================================

Write-Host "3.4 Side Effect Monitoring" -ForegroundColor Green
Write-Host ""

# Check for new firewall blocks
Write-Log "Checking for new firewall blocks..." -Level Info
$blockedConnections = Get-NetFirewallRule | Where-Object { 
    $_.Action -eq "Block" -and $_.DisplayName -like "*Darktide*" 
}
if ($blockedConnections) {
    Write-Log "WARNING: Found blocking firewall rules for Darktide" -Level Warning
    $validationResults["Side Effects"] += @{
        Title = "Firewall Blocks"
        Description = "Found blocking firewall rules that may interfere"
        Status = "Warning"
    }
} else {
    Write-Log "No blocking firewall rules found" -Level Success
    $validationResults["Side Effects"] += @{
        Title = "Firewall Blocks"
        Description = "No blocking firewall rules detected"
        Status = "Success"
    }
}

# Check for new Event Log errors (system-wide)
Write-Log "Checking for system-wide errors..." -Level Info
try {
    $systemErrors = Get-WinEvent -LogName "System" -MaxEvents 10 -ErrorAction SilentlyContinue |
        Where-Object { $_.TimeCreated -gt (Get-Date).AddMinutes(-10) -and $_.LevelDisplayName -eq "Error" }
    
    if ($systemErrors.Count -gt 0) {
        Write-Log "Found $($systemErrors.Count) recent system errors" -Level Warning
        $validationResults["Side Effects"] += @{
            Title = "System Errors"
            Description = "Found $($systemErrors.Count) recent system errors (may be unrelated)"
            Status = "Warning"
        }
    } else {
        Write-Log "No recent system errors found" -Level Success
    }
} catch {
    Write-Log "Could not check system errors: $_" -Level Warning
}

# Verify certificate revocation is still enabled (security check)
Write-Log "Verifying certificate revocation is still enabled..." -Level Info
$statePath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\WinTrust\Trust Providers\Software Publishing\State"
$certState = Get-ItemProperty -Path $statePath -Name "State" -ErrorAction SilentlyContinue

if ($certState -and $certState.State -eq 0x23C00) {
    Write-Log "WARNING: Certificate revocation is DISABLED (security risk!)" -Level Error
    $validationResults["Side Effects"] += @{
        Title = "Certificate Revocation"
        Description = "Certificate revocation is disabled globally (security risk)"
        Status = "Error"
    }
    $afterState["CertificateRevocation"] = "Disabled (Security Risk)"
} else {
    Write-Log "Certificate revocation is enabled (secure)" -Level Success
    $validationResults["Side Effects"] += @{
        Title = "Certificate Revocation"
        Description = "Certificate revocation is enabled (security preserved)"
        Status = "Success"
    }
    $afterState["CertificateRevocation"] = "Enabled"
}

# Test other applications still work
Write-Log "Testing that other applications are not affected..." -Level Info
try {
    $testUrl = "https://www.microsoft.com"
    $testResponse = Invoke-WebRequest -Uri $testUrl -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Log "Other applications connectivity: OK" -Level Success
    $validationResults["Side Effects"] += @{
        Title = "Other Applications"
        Description = "Other applications can still connect (no global impact)"
        Status = "Success"
    }
    $afterState["OtherApplications"] = "Working"
} catch {
    Write-Log "WARNING: Other applications may be affected" -Level Warning
    $validationResults["Side Effects"] += @{
        Title = "Other Applications"
        Description = "Could not verify other applications (may be network issue)"
        Status = "Warning"
    }
    $afterState["OtherApplications"] = "Unknown"
}

Write-Host ""

# ============================================================================
# 3.5 Validation Report Generation
# ============================================================================

Write-Host "3.5 Generating Validation Report" -ForegroundColor Green
Write-Host ""

$reportPath = if ($OutputPath) {
    $OutputPath
} else {
    Get-ReportPath -Type "validation"
}

# Create before/after comparison
$comparisonFindings = @{
    "Before/After Comparison" = @()
}

foreach ($key in $afterState.Keys) {
    $before = if ($beforeState.ContainsKey($key)) { $beforeState[$key] } else { "N/A" }
    $after = $afterState[$key]
    $status = if ($before -eq $after) { "Unchanged" } else { "Changed" }
    
    $comparisonFindings["Before/After Comparison"] += @{
        Title = $key
        Description = "Before: $before | After: $after | Status: $status"
        Status = if ($status -eq "Changed") { "Info" } else { "Success" }
    }
}

# Combine all findings
$allFindings = $validationResults
$allFindings["Before/After Comparison"] = $comparisonFindings["Before/After Comparison"]

New-ValidationReport -BeforeState $beforeState -AfterState $afterState -OutputPath $reportPath

Write-Host ""
Write-Host "=== Validation Phase Complete ===" -ForegroundColor Cyan
Write-Host "Report saved to: $reportPath" -ForegroundColor Green
Write-Host ""

# Summary
$totalValidations = ($validationResults.Values | Measure-Object).Count
$successCount = ($validationResults.Values | Where-Object { $_.Status -eq "Success" }).Count
$warningCount = ($validationResults.Values | Where-Object { $_.Status -eq "Warning" }).Count
$errorCount = ($validationResults.Values | Where-Object { $_.Status -eq "Error" }).Count

Write-Host "Validation Summary:" -ForegroundColor Yellow
Write-Host "  Total validations: $totalValidations" -ForegroundColor White
Write-Host "  Successful: $successCount" -ForegroundColor Green
Write-Host "  Warnings: $warningCount" -ForegroundColor $(if ($warningCount -gt 0) { "Yellow" } else { "Green" })
Write-Host "  Errors: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($errorCount -eq 0 -and $warningCount -eq 0) {
    Write-Host "All validations passed! Darktide should be working correctly." -ForegroundColor Green
} elseif ($errorCount -eq 0) {
    Write-Host "Validations completed with warnings. Review the report for details." -ForegroundColor Yellow
} else {
    Write-Host "Some validations failed. Review the report and consider running diagnostics again." -ForegroundColor Red
}

Write-Host ""

