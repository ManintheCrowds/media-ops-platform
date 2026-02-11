# PURPOSE: Main orchestrator script for Darktide diagnostic and fix workflow
# DEPENDENCIES: All phase scripts (darktide_diagnostic.ps1, darktide_fix.ps1, etc.)
# MODIFICATION NOTES: Orchestrates the complete 4-phase workflow

param(
    [string[]]$Phase = @("All"),
    [switch]$WhatIf,
    [switch]$Verbose,
    [switch]$SkipFirewall,
    [string]$BackupTimestamp
)

# Validate phase parameter
$validPhases = @("All", "Diagnostic", "Fix", "Validate", "Rollback")
foreach ($p in $Phase) {
    if ($p -notin $validPhases) {
        Write-Host "ERROR: Invalid phase '$p'. Valid phases are: $($validPhases -join ', ')" -ForegroundColor Red
        exit 1
    }
}

# Import common utilities
$commonPath = Join-Path $PSScriptRoot "darktide_common.ps1"
if (Test-Path $commonPath) {
    . $commonPath
} else {
    Write-Host "ERROR: darktide_common.ps1 not found!" -ForegroundColor Red
    exit 1
}

Write-Host "=== Darktide Workflow Orchestrator ===" -ForegroundColor Cyan
Write-Host ""

# Normalize phase parameter
if ($Phase -contains "All") {
    $phasesToRun = @("Diagnostic", "Fix", "Validate")
} else {
    $phasesToRun = $Phase
}

Write-Log "Phases to run: $($phasesToRun -join ', ')" -Level Info
if ($WhatIf) {
    Write-Log "DRY RUN MODE - No changes will be made" -Level Warning
}
Write-Host ""

# Track workflow state
$workflowState = @{
    StartTime = Get-Date
    Phases = @{}
    DiagnosticReportPath = $null
    BackupTimestamp = $null
    Errors = @()
    Warnings = @()
}

# ============================================================================
# Phase 1: Diagnostic
# ============================================================================

if ($phasesToRun -contains "Diagnostic") {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "PHASE 1: DIAGNOSTIC" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        $diagnosticScript = Join-Path $PSScriptRoot "darktide_diagnostic.ps1"
        if (-not (Test-Path $diagnosticScript)) {
            throw "Diagnostic script not found: $diagnosticScript"
        }
        
        $diagnosticParams = @{}
        if ($Verbose) { $diagnosticParams["Verbose"] = $true }
        
        $diagnosticOutput = & $diagnosticScript @diagnosticParams 2>&1
        
        # Capture diagnostic report path from output
        $diagnosticOutput | ForEach-Object {
            if ($_ -match "Report saved to: (.+)") {
                $workflowState.DiagnosticReportPath = $matches[1]
            }
            Write-Host $_
        }
        
        $workflowState.Phases["Diagnostic"] = @{
            Status = "Completed"
            Timestamp = Get-Date
        }
        
        Write-Log "Diagnostic phase completed" -Level Success
    } catch {
        $errorMsg = "Diagnostic phase failed: $_"
        Write-Log $errorMsg -Level Error
        $workflowState.Errors += $errorMsg
        $workflowState.Phases["Diagnostic"] = @{
            Status = "Failed"
            Error = $_.Exception.Message
            Timestamp = Get-Date
        }
        
        if ($phasesToRun.Count -eq 1) {
            exit 1
        }
    }
    
    Write-Host ""
    Start-Sleep -Seconds 2
}

# ============================================================================
# Phase 2: Fix
# ============================================================================

if ($phasesToRun -contains "Fix") {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "PHASE 2: FIX" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        $fixScript = Join-Path $PSScriptRoot "darktide_fix.ps1"
        if (-not (Test-Path $fixScript)) {
            throw "Fix script not found: $fixScript"
        }
        
        $fixParams = @{}
        if ($WhatIf) { $fixParams["WhatIf"] = $true }
        if ($SkipFirewall) { $fixParams["SkipFirewall"] = $true }
        if ($Verbose) { $fixParams["Verbose"] = $true }
        if ($workflowState.DiagnosticReportPath) {
            $fixParams["DiagnosticReportPath"] = $workflowState.DiagnosticReportPath
        }
        
        $fixOutput = & $fixScript @fixParams 2>&1
        
        # Capture backup timestamp from output
        $fixOutput | ForEach-Object {
            if ($_ -match "backup_(\d{8}_\d{6})") {
                $workflowState.BackupTimestamp = $matches[1]
            }
            Write-Host $_
        }
        
        $workflowState.Phases["Fix"] = @{
            Status = "Completed"
            Timestamp = Get-Date
            BackupTimestamp = $workflowState.BackupTimestamp
        }
        
        Write-Log "Fix phase completed" -Level Success
    } catch {
        $errorMsg = "Fix phase failed: $_"
        Write-Log $errorMsg -Level Error
        $workflowState.Errors += $errorMsg
        $workflowState.Phases["Fix"] = @{
            Status = "Failed"
            Error = $_.Exception.Message
            Timestamp = Get-Date
        }
        
        Write-Log "Consider running rollback if needed" -Level Warning
        if ($phasesToRun.Count -eq 1) {
            exit 1
        }
    }
    
    Write-Host ""
    Start-Sleep -Seconds 2
}

# ============================================================================
# Phase 3: Validate
# ============================================================================

if ($phasesToRun -contains "Validate") {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "PHASE 3: VALIDATE" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        $validateScript = Join-Path $PSScriptRoot "darktide_validate.ps1"
        if (-not (Test-Path $validateScript)) {
            throw "Validate script not found: $validateScript"
        }
        
        $validateParams = @{}
        if ($Verbose) { $validateParams["Verbose"] = $true }
        
        # Pass before state if available from backup
        if ($workflowState.BackupTimestamp) {
            $backupPath = Join-Path (Initialize-ReportsDirectory) "backup_$($workflowState.BackupTimestamp).json"
            if (Test-Path $backupPath) {
                $validateParams["BeforeStatePath"] = $backupPath
            }
        }
        
        $validateOutput = & $validateScript @validateParams 2>&1
        $validateOutput | ForEach-Object { Write-Host $_ }
        
        $workflowState.Phases["Validate"] = @{
            Status = "Completed"
            Timestamp = Get-Date
        }
        
        Write-Log "Validation phase completed" -Level Success
    } catch {
        $errorMsg = "Validation phase failed: $_"
        Write-Log $errorMsg -Level Error
        $workflowState.Errors += $errorMsg
        $workflowState.Phases["Validate"] = @{
            Status = "Failed"
            Error = $_.Exception.Message
            Timestamp = Get-Date
        }
        
        if ($phasesToRun.Count -eq 1) {
            exit 1
        }
    }
    
    Write-Host ""
    Start-Sleep -Seconds 2
}

# ============================================================================
# Phase 4: Rollback (if requested)
# ============================================================================

if ($phasesToRun -contains "Rollback") {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "PHASE 4: ROLLBACK" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        $rollbackScript = Join-Path $PSScriptRoot "darktide_rollback.ps1"
        if (-not (Test-Path $rollbackScript)) {
            throw "Rollback script not found: $rollbackScript"
        }
        
        $rollbackParams = @{}
        if ($WhatIf) { $rollbackParams["WhatIf"] = $true }
        if ($Verbose) { $rollbackParams["Verbose"] = $true }
        if ($BackupTimestamp) {
            $rollbackParams["BackupTimestamp"] = $BackupTimestamp
        } elseif ($workflowState.BackupTimestamp) {
            $rollbackParams["BackupTimestamp"] = $workflowState.BackupTimestamp
        }
        
        $rollbackOutput = & $rollbackScript @rollbackParams 2>&1
        $rollbackOutput | ForEach-Object { Write-Host $_ }
        
        $workflowState.Phases["Rollback"] = @{
            Status = "Completed"
            Timestamp = Get-Date
        }
        
        Write-Log "Rollback phase completed" -Level Success
    } catch {
        $errorMsg = "Rollback phase failed: $_"
        Write-Log $errorMsg -Level Error
        $workflowState.Errors += $errorMsg
        $workflowState.Phases["Rollback"] = @{
            Status = "Failed"
            Error = $_.Exception.Message
            Timestamp = Get-Date
        }
        
        exit 1
    }
    
    Write-Host ""
}

# ============================================================================
# Workflow Summary
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "WORKFLOW SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$workflowState.EndTime = Get-Date
$duration = $workflowState.EndTime - $workflowState.StartTime

Write-Host "Workflow Duration: $($duration.ToString('mm\:ss'))" -ForegroundColor White
Write-Host ""

Write-Host "Phase Status:" -ForegroundColor Yellow
$phaseKeys = $workflowState.Phases.Keys
foreach ($key in $phaseKeys) {
    $phaseData = $workflowState.Phases[$key]
    $statusColor = switch ($phaseData.Status) {
        "Completed" { "Green" }
        "Failed"    { "Red" }
        default     { "Yellow" }
    }
    Write-Host "  $key : $($phaseData.Status)" -ForegroundColor $statusColor
    if ($phaseData.Error) {
        Write-Host "    Error: $($phaseData.Error)" -ForegroundColor Red
    }
}

Write-Host ""

if ($workflowState.Errors.Count -gt 0) {
    Write-Host "Errors Encountered:" -ForegroundColor Red
    foreach ($error in $workflowState.Errors) {
        Write-Host "  - $error" -ForegroundColor Red
    }
    Write-Host ""
}

if ($workflowState.Warnings.Count -gt 0) {
    Write-Host "Warnings:" -ForegroundColor Yellow
    foreach ($warning in $workflowState.Warnings) {
        Write-Host "  - $warning" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Save workflow state
$workflowStatePath = Join-Path (Initialize-ReportsDirectory) "workflow_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$workflowState | ConvertTo-Json -Depth 10 | Out-File -FilePath $workflowStatePath -Encoding UTF8
Write-Log "Workflow state saved to: $workflowStatePath" -Level Info

Write-Host ""

# Final recommendations
if ($workflowState.Phases["Validate"].Status -eq "Completed") {
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Test Darktide connection manually" -ForegroundColor White
    Write-Host "  2. Review validation report for details" -ForegroundColor White
    if ($workflowState.BackupTimestamp) {
        Write-Host "  3. If issues persist, rollback: .\darktide_rollback.ps1 -BackupTimestamp $($workflowState.BackupTimestamp)" -ForegroundColor White
    }
} elseif ($workflowState.Phases["Fix"].Status -eq "Completed") {
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Run validation phase: .\darktide_workflow.ps1 -Phase Validate" -ForegroundColor White
    Write-Host "  2. Test Darktide connection" -ForegroundColor White
}

Write-Host ""
Write-Host "=== Workflow Complete ===" -ForegroundColor Cyan
Write-Host ""

