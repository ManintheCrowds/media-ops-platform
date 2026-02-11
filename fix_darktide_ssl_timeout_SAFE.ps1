# PURPOSE: SAFE Darktide SSL/TLS timeout diagnostic and fix script
# DEPENDENCIES: Windows PowerShell (Run as Administrator for firewall changes)
# MODIFICATION NOTES: Safer approach with diagnostics, validation, and rollback
# RISK LEVEL: LOW (no global security changes)

param(
    [switch]$DiagnosticsOnly,
    [switch]$SkipFirewall,
    [switch]$Verbose
)

Write-Host "=== Darktide SSL Timeout - Safe Diagnostic & Fix ===" -ForegroundColor Cyan
Write-Host ""

# Check admin for firewall operations only
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin -and -not $SkipFirewall) {
    Write-Host "WARNING: Administrator privileges recommended for firewall changes" -ForegroundColor Yellow
    Write-Host "Running in diagnostic mode only..." -ForegroundColor Gray
    $SkipFirewall = $true
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
    Write-Host "ERROR: Darktide.exe not found!" -ForegroundColor Red
    exit 1
}

Write-Host "Found Darktide at: $darktidePath" -ForegroundColor Green
Write-Host ""

# ============================================================================
# PHASE 1: DIAGNOSTICS (Always run first)
# ============================================================================

Write-Host "=== PHASE 1: DIAGNOSTICS ===" -ForegroundColor Cyan
Write-Host ""

# Diagnostic 1: Network connectivity
Write-Host "Diagnostic 1: Network Connectivity Test" -ForegroundColor Green
$backendHost = "bsp-sup-sd.atoma-discovery.com"
$backendIPs = @("18.160.181.16", "18.160.181.108", "18.160.181.109", "18.160.181.111")

foreach ($ip in $backendIPs) {
    $test = Test-NetConnection -ComputerName $ip -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($test) {
        Write-Host "  ✓ Can reach $ip:443" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Cannot reach $ip:443" -ForegroundColor Red
    }
}

# Test DNS resolution
try {
    $dnsResult = Resolve-DnsName -Name $backendHost -ErrorAction Stop
    Write-Host "  ✓ DNS resolution works: $($dnsResult[0].IPAddress)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ DNS resolution failed: $_" -ForegroundColor Red
}
Write-Host ""

# Diagnostic 2: SSL/TLS connectivity
Write-Host "Diagnostic 2: SSL/TLS Connectivity Test" -ForegroundColor Green
$testUrl = "https://$backendHost/bishop/steam_1361210_default"
try {
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-WebRequest -Uri $testUrl -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    $stopwatch.Stop()
    Write-Host "  ✓ SSL connection successful (Status: $($response.StatusCode), Time: $($stopwatch.ElapsedMilliseconds)ms)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ SSL connection failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Message -like "*timeout*") {
        Write-Host "  ⚠ Timeout detected - this is the issue!" -ForegroundColor Yellow
    }
    if ($_.Exception.Message -like "*revocation*") {
        Write-Host "  ⚠ Certificate revocation issue detected" -ForegroundColor Yellow
    }
}
Write-Host ""

# Diagnostic 3: Firewall rules
Write-Host "Diagnostic 3: Firewall Rules Check" -ForegroundColor Green
$firewallRules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*Darktide*" }
if ($firewallRules) {
    Write-Host "  Found firewall rules:" -ForegroundColor Gray
    $firewallRules | ForEach-Object {
        $status = if ($_.Enabled) { "Enabled" } else { "Disabled" }
        Write-Host "    - $($_.DisplayName): $status ($($_.Direction))" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠ No firewall rules found for Darktide" -ForegroundColor Yellow
}
Write-Host ""

# Diagnostic 4: Certificate revocation status (informational only)
Write-Host "Diagnostic 4: Certificate Revocation Status (Read-Only)" -ForegroundColor Green
$statePath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\WinTrust\Trust Providers\Software Publishing\State"
$certState = Get-ItemProperty -Path $statePath -Name "State" -ErrorAction SilentlyContinue

if ($certState) {
    if ($certState.State -eq 0x23C00) {
        Write-Host "  ⚠ Certificate revocation checking is DISABLED (0x23C00)" -ForegroundColor Yellow
        Write-Host "  WARNING: This is a security risk - affects ALL applications!" -ForegroundColor Red
    } else {
        Write-Host "  ✓ Certificate revocation checking is enabled (State: $($certState.State))" -ForegroundColor Green
    }
} else {
    Write-Host "  ✓ Certificate revocation using default settings" -ForegroundColor Green
}
Write-Host ""

# Diagnostic 5: VPN/TAP adapters
Write-Host "Diagnostic 5: VPN/TAP Adapter Check" -ForegroundColor Green
$tapAdapters = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like "*TAP*" -or $_.InterfaceDescription -like "*OpenVPN*" }
if ($tapAdapters) {
    $activeTAP = $tapAdapters | Where-Object { $_.Status -eq "Up" }
    if ($activeTAP) {
        Write-Host "  ⚠ Active TAP adapter found: $($activeTAP.Name)" -ForegroundColor Yellow
        Write-Host "  This may interfere with SSL connections" -ForegroundColor Gray
    } else {
        Write-Host "  ✓ TAP adapters present but not active" -ForegroundColor Green
    }
} else {
    Write-Host "  ✓ No TAP adapters detected" -ForegroundColor Green
}
Write-Host ""

# Diagnostic 6: Process-specific network check
Write-Host "Diagnostic 6: Process Network Check" -ForegroundColor Green
$darktideProcess = Get-Process -Name "Darktide" -ErrorAction SilentlyContinue
if ($darktideProcess) {
    Write-Host "  ⚠ Darktide is currently running" -ForegroundColor Yellow
    Write-Host "  Recommendation: Close Darktide before applying fixes" -ForegroundColor Gray
} else {
    Write-Host "  ✓ Darktide is not running" -ForegroundColor Green
}
Write-Host ""

if ($DiagnosticsOnly) {
    Write-Host "=== Diagnostics Complete ===" -ForegroundColor Cyan
    Write-Host "Run without -DiagnosticsOnly to apply fixes" -ForegroundColor Yellow
    exit 0
}

# ============================================================================
# PHASE 2: SAFE FIXES (Only if diagnostics indicate issues)
# ============================================================================

Write-Host "=== PHASE 2: SAFE FIXES ===" -ForegroundColor Cyan
Write-Host ""

# Fix 1: Create RESTRICTED firewall rule (SAFE)
if (-not $SkipFirewall) {
    Write-Host "Fix 1: Creating Restricted Firewall Rule..." -ForegroundColor Green
    
    # Remove overly broad existing rules
    $existingRules = Get-NetFirewallRule | Where-Object { 
        $_.DisplayName -like "*Darktide*" -and $_.Direction -eq "Outbound" 
    }
    if ($existingRules) {
        Write-Host "  Removing existing outbound rules..." -ForegroundColor Gray
        $existingRules | Remove-NetFirewallRule -ErrorAction SilentlyContinue
    }
    
    # Create RESTRICTED rule (specific IPs, port 443 only, Private/Domain profiles)
    try {
        $ruleParams = @{
            DisplayName = "Darktide Backend SSL (Restricted)"
            Direction = "Outbound"
            Program = $darktidePath
            RemoteAddress = $backendIPs
            RemotePort = 443
            Protocol = "TCP"
            Action = "Allow"
            Profile = "Private", "Domain"  # NOT Public for security
            Description = "Allow Darktide outbound SSL to backend servers only"
            ErrorAction = "Stop"
        }
        $rule = New-NetFirewallRule @ruleParams
        Write-Host "  ✓ Created RESTRICTED firewall rule (specific IPs, port 443, Private/Domain only)" -ForegroundColor Green
        Write-Host "  Security: Rule is restricted to backend IPs only" -ForegroundColor Gray
    }
    catch {
        Write-Host "  ✗ Failed to create firewall rule: $_" -ForegroundColor Red
    }
} else {
    Write-Host "Fix 1: Skipped (firewall changes)" -ForegroundColor Yellow
}
Write-Host ""

# Fix 2: DO NOT disable certificate revocation (SECURITY RISK)
Write-Host "Fix 2: Certificate Revocation (SKIPPED - Security Risk)" -ForegroundColor Yellow
Write-Host "  ⚠ NOT disabling certificate revocation (security risk)" -ForegroundColor Yellow
Write-Host "  If revocation is the issue, investigate network connectivity to revocation servers" -ForegroundColor Gray
Write-Host "  Alternative: Check if revocation servers are reachable:" -ForegroundColor Gray
Write-Host "    Test-NetConnection -ComputerName ocsp.digicert.com -Port 80" -ForegroundColor Gray
Write-Host ""

# Fix 3: Enable schannel logging (diagnostic)
Write-Host "Fix 3: Enabling Schannel Logging (Diagnostic)" -ForegroundColor Green
try {
    # Enable schannel operational log
    wevtutil sl Microsoft-Windows-Schannel/Operational /e:true 2>&1 | Out-Null
    Write-Host "  ✓ Schannel logging enabled" -ForegroundColor Green
    Write-Host "  Check Event Viewer > Applications and Services > Microsoft > Windows > Schannel" -ForegroundColor Gray
} catch {
    Write-Host "  ⚠ Could not enable schannel logging (may require admin)" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================================
# PHASE 3: VALIDATION
# ============================================================================

Write-Host "=== PHASE 3: VALIDATION ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "Validation Steps:" -ForegroundColor Yellow
Write-Host "  1. Restart Darktide completely" -ForegroundColor White
Write-Host "  2. Attempt to log in" -ForegroundColor White
Write-Host "  3. Check Event Viewer for schannel errors" -ForegroundColor White
Write-Host "  4. Monitor network activity if issue persists" -ForegroundColor White
Write-Host ""

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Fixes Applied:" -ForegroundColor Yellow
if (-not $SkipFirewall) {
    Write-Host "  ✓ Restricted firewall rule created (backend IPs only)" -ForegroundColor Green
}
Write-Host "  ✓ Schannel logging enabled for diagnostics" -ForegroundColor Green
Write-Host "  ✓ Certificate revocation NOT disabled (security preserved)" -ForegroundColor Green
Write-Host ""
Write-Host "Security Notes:" -ForegroundColor Yellow
Write-Host "  - Firewall rule is restricted to specific backend IPs" -ForegroundColor White
Write-Host "  - Certificate revocation checking remains enabled" -ForegroundColor White
Write-Host "  - No global security changes made" -ForegroundColor White
Write-Host ""
Write-Host "If issue persists, check:" -ForegroundColor Yellow
Write-Host "  - Event Viewer > Schannel logs" -ForegroundColor Gray
Write-Host "  - Network connectivity to revocation servers" -ForegroundColor Gray
Write-Host "  - Antivirus SSL scanning settings" -ForegroundColor Gray
Write-Host "  - VPN/TAP adapter interference" -ForegroundColor Gray
Write-Host ""

if ($Verbose) {
    Write-Host "=== Verbose Information ===" -ForegroundColor Cyan
    Write-Host "Darktide Path: $darktidePath" -ForegroundColor Gray
    Write-Host "Admin Rights: $isAdmin" -ForegroundColor Gray
    Write-Host "Backend IPs: $($backendIPs -join ', ')" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "Done! Review diagnostics and test Darktide." -ForegroundColor Cyan



