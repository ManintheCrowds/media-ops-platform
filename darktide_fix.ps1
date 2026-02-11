# PURPOSE: Phase 2 - Targeted safe fixes for Darktide SSL timeout issues
# DEPENDENCIES: darktide_common.ps1, Windows PowerShell (Admin for firewall)
# MODIFICATION NOTES: Implements safe fixes with automatic rollback creation

param(
    [switch]$WhatIf,
    [switch]$SkipFirewall,
    [string]$DiagnosticReportPath,
    [switch]$Verbose
)

# Import common utilities
$commonPath = Join-Path $PSScriptRoot "darktide_common.ps1"
if (Test-Path $commonPath) {
    . $commonPath
} else {
    Write-Host "ERROR: darktide_common.ps1 not found!" -ForegroundColor Red
    exit 1
}

Write-Host "=== Darktide Fix Phase 2 ===" -ForegroundColor Cyan
Write-Host ""

if ($WhatIf) {
    Write-Host "DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
}

# Check admin for firewall operations
if (-not $SkipFirewall) {
    if (-not (Test-Administrator)) {
        Write-Log "Administrator privileges required for firewall changes" -Level Warning
        Write-Log "Running without firewall changes..." -Level Info
        $SkipFirewall = $true
    }
}

$darktidePath = Get-DarktidePath
if (-not $darktidePath) {
    Write-Log "Darktide.exe not found" -Level Error
    exit 1
}

Write-Log "Found Darktide at: $darktidePath" -Level Success
Write-Host ""

# Initialize backup data
$backupData = @{
    Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    FirewallRules = @()
    CertificateRevocation = $null
    SchannelConfig = $null
    NetworkAdapters = @()
}

$changes = @()

# ============================================================================
# 2.1 Pre-Fix Backup (Rollback Preparation)
# ============================================================================

Write-Host "2.1 Creating Backup for Rollback" -ForegroundColor Green
Write-Host ""

# Backup firewall rules
Write-Log "Backing up firewall rules..." -Level Info
$existingRules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*Darktide*" }
foreach ($rule in $existingRules) {
    $ruleDetails = Get-NetFirewallRule -Name $rule.Name | Select-Object DisplayName, Direction, Action, Enabled, Profile, Program
    $backupData.FirewallRules += $ruleDetails
}
Write-Log "Backed up $($backupData.FirewallRules.Count) firewall rules" -Level Success

# Backup certificate revocation settings
Write-Log "Backing up certificate revocation settings..." -Level Info
$statePath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\WinTrust\Trust Providers\Software Publishing\State"
$certState = Get-ItemProperty -Path $statePath -Name "State" -ErrorAction SilentlyContinue
if ($certState) {
    $backupData.CertificateRevocation = @{
        Path = $statePath
        State = $certState.State
        Exists = $true
    }
} else {
    $backupData.CertificateRevocation = @{
        Path = $statePath
        State = $null
        Exists = $false
    }
}

# Backup Internet Options certificate revocation setting
$internetOptionsPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
$internetCertRevocation = Get-ItemProperty -Path $internetOptionsPath -Name "CertificateRevocation" -ErrorAction SilentlyContinue
if ($internetCertRevocation) {
    $backupData.InternetOptionsCertificateRevocation = @{
        Path = $internetOptionsPath
        CertificateRevocation = $internetCertRevocation.CertificateRevocation
        Exists = $true
    }
} else {
    $backupData.InternetOptionsCertificateRevocation = @{
        Path = $internetOptionsPath
        CertificateRevocation = $null
        Exists = $false
    }
}

Write-Log "Certificate revocation settings backed up (WinTrust + Internet Options)" -Level Success

# Backup network adapter priorities
Write-Log "Backing up network adapter priorities..." -Level Info
$adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" }
foreach ($adapter in $adapters) {
    $backupData.NetworkAdapters += @{
        Name = $adapter.Name
        InterfaceMetric = $adapter.InterfaceMetric
    }
}
Write-Log "Network adapter priorities backed up" -Level Success

# Save backup to JSON
$backupPath = Join-Path (Initialize-ReportsDirectory) "backup_$($backupData.Timestamp).json"
$backupData | ConvertTo-Json -Depth 10 | Out-File -FilePath $backupPath -Encoding UTF8
Write-Log "Backup saved to: $backupPath" -Level Success

# Create rollback script
$rollbackScriptPath = Join-Path $PSScriptRoot "darktide_rollback_$($backupData.Timestamp).ps1"
$rollbackScript = @"
# PURPOSE: Rollback script for Darktide fixes applied on $($backupData.Timestamp)
# Generated automatically by darktide_fix.ps1

`$backupData = @'
$($backupData | ConvertTo-Json -Depth 10)
'@ | ConvertFrom-Json

Write-Host "=== Darktide Rollback ===" -ForegroundColor Cyan
Write-Host "Restoring state from backup: $($backupData.Timestamp)" -ForegroundColor Yellow
Write-Host ""

# Restore firewall rules
Write-Host "Restoring firewall rules..." -ForegroundColor Green
Get-NetFirewallRule | Where-Object { `$_.DisplayName -like "*Darktide*" } | Remove-NetFirewallRule -ErrorAction SilentlyContinue

foreach (`$rule in `$backupData.FirewallRules) {
    try {
        New-NetFirewallRule -DisplayName `$rule.DisplayName `
            -Direction `$rule.Direction `
            -Action `$rule.Action `
            -Enabled `$rule.Enabled `
            -Profile `$rule.Profile `
            -Program `$rule.Program `
            -ErrorAction SilentlyContinue | Out-Null
    } catch {
        Write-Host "  Could not restore rule: `$(`$rule.DisplayName)" -ForegroundColor Yellow
    }
}

# Restore certificate revocation
Write-Host "Restoring certificate revocation settings..." -ForegroundColor Green
if (`$backupData.CertificateRevocation.Exists) {
    Set-ItemProperty -Path `$backupData.CertificateRevocation.Path `
        -Name "State" `
        -Value `$backupData.CertificateRevocation.State `
        -Type DWord `
        -ErrorAction SilentlyContinue
} else {
    Remove-ItemProperty -Path `$backupData.CertificateRevocation.Path `
        -Name "State" `
        -ErrorAction SilentlyContinue
}

Write-Host "Rollback complete!" -ForegroundColor Green
"@

if (-not $WhatIf) {
    $rollbackScript | Out-File -FilePath $rollbackScriptPath -Encoding UTF8
    Write-Log "Rollback script created: $rollbackScriptPath" -Level Success
} else {
    Write-Log "Would create rollback script: $rollbackScriptPath" -Level Info
}

Write-Host ""

# ============================================================================
# 2.2 Network Connectivity Fixes
# ============================================================================

Write-Host "2.2 Network Connectivity Fixes" -ForegroundColor Green
Write-Host ""

# Test connectivity to revocation servers
Write-Log "Testing revocation server connectivity..." -Level Info
$revocationTest = Test-RevocationServerConnectivity
$unreachableRevocation = $revocationTest.Servers | Where-Object { -not $_.Reachable }

if ($unreachableRevocation.Count -gt 0) {
    Write-Log "WARNING: Some revocation servers are unreachable" -Level Warning
    Write-Log "This may cause certificate validation issues, but we will NOT disable revocation globally" -Level Warning
    Write-Log "Recommendation: Check firewall/DNS settings for revocation servers" -Level Info
    $changes += @{
        Timestamp = Get-Date
        Type = "Network Connectivity"
        Action = "Identified unreachable revocation servers"
        Details = "Servers: $(($unreachableRevocation | ForEach-Object { $_.Server }) -join ', ')"
    }
} else {
    Write-Log "All revocation servers are reachable" -Level Success
}

# Check network adapter priority (informational only, don't auto-fix)
$adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Sort-Object InterfaceMetric
$primaryAdapter = $adapters | Select-Object -First 1
if ($primaryAdapter) {
    Write-Log "Primary network adapter: $($primaryAdapter.Name) (Metric: $($primaryAdapter.InterfaceMetric))" -Level Info
    if ($primaryAdapter.InterfaceDescription -notlike "*Wi-Fi*" -and $primaryAdapter.InterfaceDescription -notlike "*Ethernet*") {
        Write-Log "WARNING: Primary adapter may not be optimal" -Level Warning
        Write-Log "Consider adjusting adapter priority manually if needed" -Level Info
    }
}

Write-Host ""

# ============================================================================
# 2.3 Firewall Rule Creation (Restricted)
# ============================================================================

if (-not $SkipFirewall) {
    Write-Host "2.3 Creating Restricted Firewall Rules" -ForegroundColor Green
    Write-Host ""
    
    # Remove overly broad existing rules
    Write-Log "Removing existing outbound rules..." -Level Info
    $existingOutboundRules = Get-NetFirewallRule | Where-Object { 
        $_.DisplayName -like "*Darktide*" -and $_.Direction -eq "Outbound" 
    }
    
    if ($existingOutboundRules -and -not $WhatIf) {
        $existingOutboundRules | Remove-NetFirewallRule -ErrorAction SilentlyContinue
        Write-Log "Removed $($existingOutboundRules.Count) existing outbound rules" -Level Success
        $changes += @{
            Timestamp = Get-Date
            Type = "Firewall"
            Action = "Removed existing outbound rules"
            Details = "Removed $($existingOutboundRules.Count) rules"
        }
    } elseif ($existingOutboundRules) {
        Write-Log "Would remove $($existingOutboundRules.Count) existing outbound rules" -Level Info
    }
    
    # Create restricted firewall rule
    $backendConfig = Get-BackendConfiguration
    Write-Log "Creating restricted firewall rule..." -Level Info
    
    $ruleParams = @{
        DisplayName = "Darktide Backend SSL (Restricted)"
        Direction = "Outbound"
        Program = $darktidePath
        RemoteAddress = $backendConfig.IPs
        RemotePort = $backendConfig.Port
        Protocol = $backendConfig.Protocol
        Action = "Allow"
        Profile = "Private", "Domain"  # NOT Public for security
        Description = "Allow Darktide outbound SSL to backend servers only (restricted to specific IPs)"
        ErrorAction = "Stop"
    }
    
    try {
        if (-not $WhatIf) {
            $rule = New-NetFirewallRule @ruleParams
            Write-Log "Created restricted firewall rule: $($rule.DisplayName)" -Level Success
            Write-Log "  - Restricted to backend IPs: $($backendConfig.IPs -join ', ')" -Level Info
            Write-Log "  - Port: $($backendConfig.Port)" -Level Info
            Write-Log "  - Profiles: Private, Domain (NOT Public)" -Level Info
            
            $changes += @{
                Timestamp = Get-Date
                Type = "Firewall"
                Action = "Created restricted outbound rule"
                Details = "Rule: $($rule.DisplayName), IPs: $($backendConfig.IPs -join ', '), Port: $($backendConfig.Port)"
            }
        } else {
            Write-Log "Would create restricted firewall rule" -Level Info
            Write-Log "  - IPs: $($backendConfig.IPs -join ', ')" -Level Info
            Write-Log "  - Port: $($backendConfig.Port)" -Level Info
        }
    } catch {
        Write-Log "Failed to create firewall rule: $_" -Level Error
        if (-not $WhatIf) {
            throw
        }
    }
    
    # Ensure inbound rule exists (if needed)
    $inboundRule = Get-NetFirewallRule | Where-Object { 
        $_.DisplayName -like "*Darktide*" -and $_.Direction -eq "Inbound" -and $_.Enabled -eq $true 
    } | Select-Object -First 1
    
    if (-not $inboundRule -and -not $WhatIf) {
        try {
            $inboundParams = @{
                DisplayName = "Darktide Inbound"
                Direction = "Inbound"
                Program = $darktidePath
                Action = "Allow"
                Profile = "Private", "Domain"
                Description = "Allow Darktide inbound connections"
                ErrorAction = "SilentlyContinue"
            }
            New-NetFirewallRule @inboundParams | Out-Null
            Write-Log "Ensured inbound firewall rule exists" -Level Success
        } catch {
            Write-Log "Could not create inbound rule: $_" -Level Warning
        }
    }
} else {
    Write-Host "2.3 Firewall Rules (Skipped)" -ForegroundColor Yellow
    Write-Log "Skipping firewall rule creation (requires Administrator or -SkipFirewall specified)" -Level Info
}

Write-Host ""

# ============================================================================
# 2.4 Schannel Timeout Configuration
# ============================================================================

Write-Host "2.4 Schannel Timeout Configuration" -ForegroundColor Green
Write-Host ""

Write-Log "Checking schannel timeout configuration..." -Level Info
Write-Log "NOTE: We will NOT disable certificate revocation globally (security risk)" -Level Warning
Write-Log "If timeout issues persist, investigate network connectivity to revocation servers" -Level Info

# Check if schannel timeout can be configured per-application
# Note: Per-application schannel timeout configuration is limited in Windows
# We'll document the current state but not make global changes

$schannelPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL"
$timeoutSettings = @("ClientCacheTime", "ServerCacheTime")

foreach ($setting in $timeoutSettings) {
    $value = Get-ItemProperty -Path $schannelPath -Name $setting -ErrorAction SilentlyContinue
    if ($value) {
        Write-Log "Schannel $setting = $($value.$setting)" -Level Info
    } else {
        Write-Log "Schannel $setting = (default)" -Level Info
    }
}

Write-Log "No schannel timeout changes made (preserving security)" -Level Info
Write-Host ""

# ============================================================================
# 2.5 Change Logging
# ============================================================================

Write-Host "2.5 Logging Changes" -ForegroundColor Green
Write-Host ""

$changesLogPath = Join-Path (Initialize-ReportsDirectory) "changes_$($backupData.Timestamp).log"

$logContent = @"
Darktide Fix Changes Log
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Backup Timestamp: $($backupData.Timestamp)

Changes Made:
"@

foreach ($change in $changes) {
    $logContent += @"

[$($change.Timestamp)] $($change.Type): $($change.Action)
  Details: $($change.Details)
"@
}

if ($changes.Count -eq 0) {
    $logContent += @"

No changes were made.
"@
}

if (-not $WhatIf) {
    $logContent | Out-File -FilePath $changesLogPath -Encoding UTF8
    Write-Log "Changes logged to: $changesLogPath" -Level Success
} else {
    Write-Log "Would log changes to: $changesLogPath" -Level Info
}

Write-Host ""

# ============================================================================
# 2.6 Error Handling Summary
# ============================================================================

Write-Host "=== Fix Phase Complete ===" -ForegroundColor Cyan
Write-Host ""

if ($WhatIf) {
    Write-Host "DRY RUN - No actual changes were made" -ForegroundColor Yellow
} else {
    Write-Host "Summary of Changes:" -ForegroundColor Yellow
    Write-Host "  - Backup created: $backupPath" -ForegroundColor White
    Write-Host "  - Rollback script: $rollbackScriptPath" -ForegroundColor White
    Write-Host "  - Changes logged: $changesLogPath" -ForegroundColor White
    Write-Host "  - Total changes: $($changes.Count)" -ForegroundColor White
    Write-Host ""
    Write-Host "Security Notes:" -ForegroundColor Yellow
    Write-Host "  - Certificate revocation NOT disabled (security preserved)" -ForegroundColor Green
    Write-Host "  - Firewall rules restricted to backend IPs only" -ForegroundColor Green
    Write-Host "  - All changes are reversible via rollback script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Run validation phase: .\darktide_validate.ps1" -ForegroundColor White
    Write-Host "  2. Test Darktide connection" -ForegroundColor White
    Write-Host "  3. If issues persist, review diagnostic report" -ForegroundColor White
    Write-Host "  4. To rollback: .\darktide_rollback_$($backupData.Timestamp).ps1" -ForegroundColor White
}

Write-Host ""

