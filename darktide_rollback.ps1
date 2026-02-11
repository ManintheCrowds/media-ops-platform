# PURPOSE: Phase 4 - Rollback script to restore original state
# DEPENDENCIES: darktide_common.ps1, Windows PowerShell (Admin for firewall)
# MODIFICATION NOTES: Restores system to state before fixes were applied

param(
    [string]$BackupTimestamp,
    [string]$BackupPath,
    [switch]$WhatIf,
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

Write-Host "=== Darktide Rollback Phase 4 ===" -ForegroundColor Cyan
Write-Host ""

if ($WhatIf) {
    Write-Host "DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
}

# Check admin for firewall operations
if (-not (Test-Administrator)) {
    Write-Log "Administrator privileges required for firewall restoration" -Level Warning
    Write-Log "Some operations may be skipped..." -Level Info
}

# Find backup file
$backupFile = $null

if ($BackupPath -and (Test-Path $BackupPath)) {
    $backupFile = $BackupPath
} elseif ($BackupTimestamp) {
    $backupFile = Join-Path (Initialize-ReportsDirectory) "backup_$BackupTimestamp.json"
    if (-not (Test-Path $backupFile)) {
        Write-Log "Backup file not found: $backupFile" -Level Error
        exit 1
    }
} else {
    # List available backups
    Write-Host "Available backups:" -ForegroundColor Yellow
    $reportsDir = Initialize-ReportsDirectory
    $backups = Get-ChildItem -Path $reportsDir -Filter "backup_*.json" | Sort-Object LastWriteTime -Descending
    
    if ($backups.Count -eq 0) {
        Write-Log "No backup files found" -Level Error
        exit 1
    }
    
    Write-Host ""
    for ($i = 0; $i -lt $backups.Count; $i++) {
        $backup = $backups[$i]
        $timestamp = $backup.Name -replace "backup_", "" -replace "\.json", ""
        Write-Host "  [$i] $timestamp ($($backup.LastWriteTime))" -ForegroundColor White
    }
    Write-Host ""
    
    $selection = Read-Host "Select backup to restore (0-$($backups.Count - 1))"
    if ($selection -match '^\d+$' -and [int]$selection -ge 0 -and [int]$selection -lt $backups.Count) {
        $backupFile = $backups[[int]$selection].FullName
    } else {
        Write-Log "Invalid selection" -Level Error
        exit 1
    }
}

# Load backup data
Write-Log "Loading backup from: $backupFile" -Level Info
try {
    $backupData = Get-Content $backupFile | ConvertFrom-Json
    Write-Log "Backup loaded successfully (Timestamp: $($backupData.Timestamp))" -Level Success
} catch {
    Write-Log "Failed to load backup: $_" -Level Error
    exit 1
}

# Verify backup integrity
Write-Log "Verifying backup integrity..." -Level Info
$requiredFields = @("Timestamp", "FirewallRules", "CertificateRevocation")
$missingFields = $requiredFields | Where-Object { -not $backupData.PSObject.Properties.Name -contains $_ }

if ($missingFields) {
    Write-Log "WARNING: Backup missing required fields: $($missingFields -join ', ')" -Level Warning
} else {
    Write-Log "Backup integrity verified" -Level Success
}

Write-Host ""

# ============================================================================
# 4.2 Firewall Rule Restoration
# ============================================================================

Write-Host "4.2 Restoring Firewall Rules" -ForegroundColor Green
Write-Host ""

# Remove fix-created firewall rules
Write-Log "Removing fix-created firewall rules..." -Level Info
$fixCreatedRules = Get-NetFirewallRule | Where-Object { 
    $_.DisplayName -like "*Darktide*" -and 
    ($_.DisplayName -like "*Restricted*" -or $_.DisplayName -like "*Backend*" -or $_.DisplayName -like "*SSL*")
}

if ($fixCreatedRules) {
    if (-not $WhatIf) {
        $fixCreatedRules | Remove-NetFirewallRule -ErrorAction SilentlyContinue
        Write-Log "Removed $($fixCreatedRules.Count) fix-created firewall rules" -Level Success
    } else {
        Write-Log "Would remove $($fixCreatedRules.Count) fix-created firewall rules" -Level Info
    }
} else {
    Write-Log "No fix-created firewall rules found to remove" -Level Info
}

# Restore original firewall rules
if ($backupData.FirewallRules -and $backupData.FirewallRules.Count -gt 0) {
    Write-Log "Restoring $($backupData.FirewallRules.Count) original firewall rules..." -Level Info
    
    foreach ($rule in $backupData.FirewallRules) {
        try {
            if (-not $WhatIf) {
                $ruleParams = @{
                    DisplayName = $rule.DisplayName
                    Direction = $rule.Direction
                    Action = $rule.Action
                    Enabled = $rule.Enabled
                    ErrorAction = "SilentlyContinue"
                }
                
                if ($rule.Profile) {
                    $ruleParams["Profile"] = $rule.Profile
                }
                if ($rule.Program) {
                    $ruleParams["Program"] = $rule.Program
                }
                
                New-NetFirewallRule @ruleParams | Out-Null
                Write-Log "  Restored: $($rule.DisplayName)" -Level Success
            } else {
                Write-Log "  Would restore: $($rule.DisplayName)" -Level Info
            }
        } catch {
            Write-Log "  Could not restore rule: $($rule.DisplayName) - $_" -Level Warning
        }
    }
} else {
    Write-Log "No original firewall rules to restore" -Level Info
}

Write-Host ""

# ============================================================================
# 4.3 Registry Restoration
# ============================================================================

Write-Host "4.3 Restoring Registry Settings" -ForegroundColor Green
Write-Host ""

# Restore certificate revocation settings
if ($backupData.CertificateRevocation) {
    Write-Log "Restoring certificate revocation settings..." -Level Info
    $statePath = $backupData.CertificateRevocation.Path
    
    try {
        if ($backupData.CertificateRevocation.Exists) {
            if (-not $WhatIf) {
                # Ensure path exists
                $parentPath = Split-Path $statePath -Parent
                if (-not (Test-Path $parentPath)) {
                    New-Item -Path $parentPath -Force | Out-Null
                }
                if (-not (Test-Path $statePath)) {
                    New-Item -Path $statePath -Force | Out-Null
                }
                
                Set-ItemProperty -Path $statePath `
                    -Name "State" `
                    -Value $backupData.CertificateRevocation.State `
                    -Type DWord `
                    -ErrorAction Stop
                
                Write-Log "Restored certificate revocation state: $($backupData.CertificateRevocation.State)" -Level Success
            } else {
                Write-Log "Would restore certificate revocation state: $($backupData.CertificateRevocation.State)" -Level Info
            }
        } else {
            if (-not $WhatIf) {
                Remove-ItemProperty -Path $statePath -Name "State" -ErrorAction SilentlyContinue
                Write-Log "Removed certificate revocation override (restored to default)" -Level Success
            } else {
                Write-Log "Would remove certificate revocation override" -Level Info
            }
        }
    } catch {
        Write-Log "Could not restore certificate revocation: $_" -Level Error
    }
} else {
    Write-Log "No certificate revocation backup found" -Level Warning
}

# Restore Internet Options certificate revocation
if ($backupData.InternetOptionsCertificateRevocation) {
    Write-Log "Restoring Internet Options certificate revocation..." -Level Info
    $internetOptionsPath = $backupData.InternetOptionsCertificateRevocation.Path
    
    try {
        if ($backupData.InternetOptionsCertificateRevocation.Exists) {
            if (-not $WhatIf) {
                Set-ItemProperty -Path $internetOptionsPath `
                    -Name "CertificateRevocation" `
                    -Value $backupData.InternetOptionsCertificateRevocation.CertificateRevocation `
                    -Type DWord `
                    -ErrorAction Stop
                
                Write-Log "Restored Internet Options certificate revocation: $($backupData.InternetOptionsCertificateRevocation.CertificateRevocation)" -Level Success
            } else {
                Write-Log "Would restore Internet Options certificate revocation: $($backupData.InternetOptionsCertificateRevocation.CertificateRevocation)" -Level Info
            }
        } else {
            if (-not $WhatIf) {
                Remove-ItemProperty -Path $internetOptionsPath -Name "CertificateRevocation" -ErrorAction SilentlyContinue
                Write-Log "Removed Internet Options certificate revocation override (restored to default)" -Level Success
            } else {
                Write-Log "Would remove Internet Options certificate revocation override" -Level Info
            }
        }
    } catch {
        Write-Log "Could not restore Internet Options certificate revocation: $_" -Level Error
    }
}

Write-Host ""

# ============================================================================
# 4.4 Network Configuration Restoration
# ============================================================================

Write-Host "4.4 Restoring Network Configuration" -ForegroundColor Green
Write-Host ""

# Note: Network adapter priorities are typically not changed by the fix script
# This section is for completeness and future extensibility

if ($backupData.NetworkAdapters -and $backupData.NetworkAdapters.Count -gt 0) {
    Write-Log "Network adapter priorities were not modified by fixes" -Level Info
    Write-Log "No network adapter restoration needed" -Level Success
} else {
    Write-Log "No network adapter backup found (not modified)" -Level Info
}

Write-Host ""

# ============================================================================
# 4.5 Rollback Validation
# ============================================================================

Write-Host "4.5 Validating Rollback" -ForegroundColor Green
Write-Host ""

$rollbackValidation = @{
    FirewallRules = $false
    CertificateRevocation = $false
}

# Verify firewall rules
Write-Log "Verifying firewall rule restoration..." -Level Info
$currentRules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*Darktide*" }
$fixCreatedRules = $currentRules | Where-Object { 
    $_.DisplayName -like "*Restricted*" -or $_.DisplayName -like "*Backend*" -or $_.DisplayName -like "*SSL*"
}

if ($fixCreatedRules.Count -eq 0) {
    Write-Log "Firewall rules: OK (fix-created rules removed)" -Level Success
    $rollbackValidation.FirewallRules = $true
} else {
    Write-Log "Firewall rules: WARNING (some fix-created rules still exist)" -Level Warning
}

# Verify certificate revocation
Write-Log "Verifying certificate revocation restoration..." -Level Info
$statePath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\WinTrust\Trust Providers\Software Publishing\State"
$currentState = Get-ItemProperty -Path $statePath -Name "State" -ErrorAction SilentlyContinue

if ($backupData.CertificateRevocation.Exists) {
    if ($currentState -and $currentState.State -eq $backupData.CertificateRevocation.State) {
        Write-Log "Certificate revocation: OK (restored to original state)" -Level Success
        $rollbackValidation.CertificateRevocation = $true
    } else {
        Write-Log "Certificate revocation: WARNING (state mismatch)" -Level Warning
    }
} else {
    if (-not $currentState) {
        Write-Log "Certificate revocation: OK (restored to default)" -Level Success
        $rollbackValidation.CertificateRevocation = $true
    } else {
        Write-Log "Certificate revocation: WARNING (should be default but override exists)" -Level Warning
    }
}

Write-Host ""

# ============================================================================
# Summary
# ============================================================================

Write-Host "=== Rollback Complete ===" -ForegroundColor Cyan
Write-Host ""

if ($WhatIf) {
    Write-Host "DRY RUN - No actual changes were made" -ForegroundColor Yellow
} else {
    Write-Host "Rollback Summary:" -ForegroundColor Yellow
    Write-Host "  Backup restored: $($backupData.Timestamp)" -ForegroundColor White
    Write-Host "  Firewall rules: $(if ($rollbackValidation.FirewallRules) { 'Restored' } else { 'Partial' })" -ForegroundColor White
    Write-Host "  Certificate revocation: $(if ($rollbackValidation.CertificateRevocation) { 'Restored' } else { 'Partial' })" -ForegroundColor White
    Write-Host ""
    
    if ($rollbackValidation.FirewallRules -and $rollbackValidation.CertificateRevocation) {
        Write-Host "Rollback completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Rollback completed with warnings. Review the output above." -ForegroundColor Yellow
    }
}

Write-Host ""

