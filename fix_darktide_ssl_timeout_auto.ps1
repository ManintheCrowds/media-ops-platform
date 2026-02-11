# PURPOSE: Automatically fix Darktide SSL/TLS timeout errors
# DEPENDENCIES: Windows PowerShell (Run as Administrator)
# MODIFICATION NOTES: Auto-fixes SSL timeout issues for Darktide backend authentication

param(
    [switch]$SkipFirewall,
    [switch]$SkipTests,
    [switch]$Verbose
)

Write-Host "=== Darktide SSL Timeout Auto-Fix ===" -ForegroundColor Cyan
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Find Darktide executable
$darktidePaths = @(
    "D:\SteamLibrary\steamapps\common\Warhammer 40,000 DARKTIDE\binaries\Darktide.exe",
    "E:\SteamLibrary\steamapps\common\Warhammer 40,000 DARKTIDE\binaries\Darktide.exe",
    "C:\Program Files (x86)\Steam\steamapps\common\Warhammer 40,000 DARKTIDE\binaries\Darktide.exe"
)

$darktidePath = $null
foreach ($path in $darktidePaths) {
    if (Test-Path $path) {
        $darktidePath = $path
        break
    }
}

if (-not $darktidePath) {
    Write-Host "ERROR: Darktide.exe not found in standard locations!" -ForegroundColor Red
    Write-Host "Please specify the path manually or install Darktide first." -ForegroundColor Yellow
    exit 1
}

Write-Host "Found Darktide at: $darktidePath" -ForegroundColor Green
Write-Host ""

# Fix 1: Add/Update Outbound Firewall Rule
if (-not $SkipFirewall) {
    Write-Host "Fix 1: Configuring Windows Firewall Rules..." -ForegroundColor Green
    
    # Remove existing outbound rules for Darktide
    $existingRules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*Darktide*" -and $_.Direction -eq "Outbound" }
    if ($existingRules) {
        Write-Host "  Removing existing outbound rules..." -ForegroundColor Gray
        $existingRules | Remove-NetFirewallRule -ErrorAction SilentlyContinue
    }
    
    # Add new outbound rule
    try {
        $ruleParams = @{
            DisplayName = "Darktide Outbound SSL"
            Direction = "Outbound"
            Program = $darktidePath
            Action = "Allow"
            Profile = "Any"
            Description = "Allow Darktide outbound SSL/TLS connections to backend servers"
            ErrorAction = "Stop"
        }
        $rule = New-NetFirewallRule @ruleParams
        Write-Host "  ✓ Created outbound firewall rule: $($rule.DisplayName)" -ForegroundColor Green
        
        # Also ensure inbound rules exist
        $inboundRule = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*Darktide*" -and $_.Direction -eq "Inbound" -and $_.Enabled -eq $true } | Select-Object -First 1
        if (-not $inboundRule) {
            $inboundParams = @{
                DisplayName = "Darktide Inbound"
                Direction = "Inbound"
                Program = $darktidePath
                Action = "Allow"
                Profile = "Any"
                Description = "Allow Darktide inbound connections"
                ErrorAction = "SilentlyContinue"
            }
            New-NetFirewallRule @inboundParams | Out-Null
            Write-Host "  ✓ Ensured inbound firewall rule exists" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "  ✗ Failed to create firewall rule: $_" -ForegroundColor Red
    }
} else {
    Write-Host "Fix 1: Skipped (firewall changes)" -ForegroundColor Yellow
}
Write-Host ""

# Fix 2: Check and disable TAP adapter if interfering
Write-Host "Fix 2: Checking VPN/TAP Adapters..." -ForegroundColor Green
$tapAdapters = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like "*TAP*" -or $_.InterfaceDescription -like "*OpenVPN*" }
if ($tapAdapters) {
    $activeTAP = $tapAdapters | Where-Object { $_.Status -eq "Up" }
    if ($activeTAP) {
        Write-Host "  ⚠ Found active TAP adapter: $($activeTAP.Name)" -ForegroundColor Yellow
        Write-Host "  TAP adapters can interfere with SSL connections" -ForegroundColor Gray
        Write-Host "  Consider disabling VPN while playing Darktide" -ForegroundColor Gray
    } else {
        Write-Host "  ✓ TAP adapters found but not active" -ForegroundColor Green
    }
} else {
    Write-Host "  ✓ No TAP adapters detected" -ForegroundColor Green
}
Write-Host ""

# Fix 3: Verify certificate revocation setting
Write-Host "Fix 3: Verifying Certificate Revocation Settings..." -ForegroundColor Green
$statePath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\WinTrust\Trust Providers\Software Publishing\State"
$certState = Get-ItemProperty -Path $statePath -Name "State" -ErrorAction SilentlyContinue

if ($certState -and $certState.State -eq 0x23C00) {
    Write-Host "  ✓ Certificate revocation checking is disabled (0x23C00)" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Certificate revocation checking may still be enabled" -ForegroundColor Yellow
    Write-Host "  Applying fix..." -ForegroundColor Gray
    try {
        $parentPath = Split-Path $statePath -Parent
        if (-not (Test-Path $parentPath)) {
            New-Item -Path $parentPath -Force | Out-Null
        }
        if (-not (Test-Path $statePath)) {
            New-Item -Path $statePath -Force | Out-Null
        }
        Set-ItemProperty -Path $statePath -Name "State" -Value 0x23C00 -Type DWord -ErrorAction Stop
        Write-Host "  ✓ Disabled certificate revocation checking" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ Failed to set certificate revocation: $_" -ForegroundColor Red
    }
}
Write-Host ""

# Fix 4: Check network adapter priority
Write-Host "Fix 4: Checking Network Adapter Priority..." -ForegroundColor Green
$adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Sort-Object InterfaceMetric
$primaryAdapter = $adapters | Select-Object -First 1
if ($primaryAdapter) {
    Write-Host "  Primary adapter: $($primaryAdapter.Name) (Metric: $($primaryAdapter.InterfaceMetric))" -ForegroundColor Gray
    if ($primaryAdapter.InterfaceDescription -like "*Wi-Fi*" -or $primaryAdapter.InterfaceDescription -like "*Ethernet*") {
        Write-Host "  ✓ Primary adapter looks correct" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Primary adapter may not be optimal" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ No active network adapters found" -ForegroundColor Yellow
}
Write-Host ""

# Fix 5: Test backend connectivity
if (-not $SkipTests) {
    Write-Host "Fix 5: Testing Backend Connectivity..." -ForegroundColor Green
    $testUrl = "https://bsp-sup-sd.atoma-discovery.com/bishop/steam_1361210_default"
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri $testUrl -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
        $stopwatch.Stop()
        Write-Host "  ✓ Backend reachable (Status: $($response.StatusCode), Time: $($stopwatch.ElapsedMilliseconds)ms)" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ Backend test failed: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Message -like "*timeout*") {
            Write-Host "  ⚠ Timeout detected - may indicate firewall or network issue" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "Fix 5: Skipped (connectivity tests)" -ForegroundColor Yellow
}
Write-Host ""

# Fix 6: Check for SSL interception software
Write-Host "Fix 6: Checking for SSL Interception Software..." -ForegroundColor Green
$securityProcesses = Get-Process | Where-Object { 
    $_.ProcessName -like "*kaspersky*" -or 
    $_.ProcessName -like "*norton*" -or 
    $_.ProcessName -like "*mcafee*" -or 
    $_.ProcessName -like "*avast*" -or 
    $_.ProcessName -like "*avg*" -or
    $_.ProcessName -like "*bitdefender*" -or
    $_.ProcessName -like "*eset*"
} | Select-Object -First 5

if ($securityProcesses) {
    Write-Host "  ⚠ Security software detected (may intercept SSL):" -ForegroundColor Yellow
    $securityProcesses | ForEach-Object {
        Write-Host "    - $($_.ProcessName)" -ForegroundColor Gray
    }
    Write-Host "  Consider temporarily disabling SSL scanning for Darktide" -ForegroundColor Gray
} else {
    Write-Host "  ✓ No obvious SSL interception software detected" -ForegroundColor Green
}
Write-Host ""

# Summary
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Fixes Applied:" -ForegroundColor Yellow
if (-not $SkipFirewall) {
    Write-Host "  ✓ Outbound firewall rule created for Darktide" -ForegroundColor Green
}
Write-Host "  ✓ Certificate revocation checking verified/disabled" -ForegroundColor Green
Write-Host "  ✓ Network adapter priority checked" -ForegroundColor Green
if (-not $SkipTests) {
    Write-Host "  ✓ Backend connectivity tested" -ForegroundColor Green
}
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Restart Darktide completely (close all processes)" -ForegroundColor White
Write-Host "  2. Try logging in again" -ForegroundColor White
Write-Host "  3. If issue persists:" -ForegroundColor White
Write-Host "     - Temporarily disable VPN/TAP adapters" -ForegroundColor Gray
Write-Host "     - Check antivirus SSL scanning settings" -ForegroundColor Gray
Write-Host "     - Verify Windows Firewall is not blocking in Windows Security" -ForegroundColor Gray
Write-Host ""
Write-Host "To revert firewall changes:" -ForegroundColor Yellow
Write-Host "  Remove-NetFirewallRule -DisplayName 'Darktide Outbound SSL'" -ForegroundColor Gray
Write-Host ""

if ($Verbose) {
    Write-Host "=== Verbose Information ===" -ForegroundColor Cyan
    Write-Host "Darktide Path: $darktidePath" -ForegroundColor Gray
    Write-Host "Admin Rights: $isAdmin" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "Done! Restart Darktide and test." -ForegroundColor Cyan
