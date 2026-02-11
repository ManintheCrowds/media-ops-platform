# PURPOSE: Fix Internet Options certificate revocation setting that overrides WinTrust registry
# DEPENDENCIES: Windows PowerShell
# MODIFICATION NOTES: Addresses CRYPT_E_REVOCATION_OFFLINE error when Internet Options overrides registry

param(
    [switch]$WhatIf,
    [switch]$Verbose
)

Write-Host "=== Fix Internet Options Certificate Revocation ===" -ForegroundColor Cyan
Write-Host ""

$internetOptionsPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
$currentSetting = Get-ItemProperty -Path $internetOptionsPath -Name "CertificateRevocation" -ErrorAction SilentlyContinue

Write-Host "Current Settings:" -ForegroundColor Yellow
$certRevStatus = if ($currentSetting) { $currentSetting.CertificateRevocation } else { "Default (enabled)" }
Write-Host "  Internet Options CertificateRevocation: $certRevStatus" -ForegroundColor White

$winTrustPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\WinTrust\Trust Providers\Software Publishing\State"
$winTrustState = Get-ItemProperty -Path $winTrustPath -Name "State" -ErrorAction SilentlyContinue
$winTrustStatus = if ($winTrustState) { "0x$($winTrustState.State.ToString('X'))" } else { "Default" }
Write-Host "  WinTrust State: $winTrustStatus" -ForegroundColor White
Write-Host ""

if ($currentSetting -and $currentSetting.CertificateRevocation -eq 1) {
    Write-Host "ISSUE FOUND:" -ForegroundColor Red
    Write-Host "  Internet Options has certificate revocation ENABLED (1)" -ForegroundColor Yellow
    Write-Host "  This overrides WinTrust registry settings and causes CRYPT_E_REVOCATION_OFFLINE errors" -ForegroundColor Yellow
    Write-Host ""
    
    if (-not $WhatIf) {
        Write-Host "Fixing: Disabling certificate revocation in Internet Options..." -ForegroundColor Green
        try {
            Set-ItemProperty -Path $internetOptionsPath -Name "CertificateRevocation" -Value 0 -Type DWord -ErrorAction Stop
            
            Write-Host "  ✓ Disabled certificate revocation in Internet Options" -ForegroundColor Green
            Write-Host ""
            Write-Host "NOTE: This is a security trade-off. Certificate revocation checking is disabled." -ForegroundColor Yellow
            Write-Host "If you want to keep revocation enabled, fix network connectivity to revocation servers instead." -ForegroundColor Gray
        } catch {
            Write-Host "  ✗ Failed to update Internet Options: $_" -ForegroundColor Red
            Write-Host ""
            Write-Host "Manual fix:" -ForegroundColor Yellow
            Write-Host "  1. Open Internet Options (inetcpl.cpl)" -ForegroundColor White
            Write-Host "  2. Go to Advanced tab" -ForegroundColor White
            Write-Host "  3. Under Security, uncheck 'Check for server certificate revocation'" -ForegroundColor White
            Write-Host "  4. Click OK" -ForegroundColor White
        }
    } else {
        Write-Host "DRY RUN: Would disable certificate revocation in Internet Options" -ForegroundColor Yellow
    }
} else {
    Write-Host "Internet Options certificate revocation is not explicitly enabled" -ForegroundColor Green
    Write-Host "The issue may be elsewhere. Check:" -ForegroundColor Yellow
    Write-Host "  - Network connectivity to revocation servers" -ForegroundColor White
    Write-Host "  - Firewall blocking revocation servers" -ForegroundColor White
    Write-Host "  - DNS resolution for revocation servers" -ForegroundColor White
}

Write-Host ""
Write-Host "To revert this change:" -ForegroundColor Yellow
Write-Host '  Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name CertificateRevocation -Value 1' -ForegroundColor Gray
Write-Host ""
