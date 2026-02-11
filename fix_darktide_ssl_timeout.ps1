# PURPOSE: Fix Darktide SSL/TLS timeout error (schannel: timed out sending data)
# DEPENDENCIES: Windows PowerShell (Run as Administrator)
# MODIFICATION NOTES: Created to troubleshoot Darktide backend SSL timeout errors

Write-Host "=== Darktide SSL/TLS Timeout Fix ===" -ForegroundColor Cyan
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator. Some fixes may not work." -ForegroundColor Yellow
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
}

# Analysis of the error
Write-Host "Error Analysis:" -ForegroundColor Yellow
Write-Host "  Previous: CRYPT_E_REVOCATION_OFFLINE (FIXED)" -ForegroundColor Green
Write-Host "  Current:  schannel: timed out sending data (bytes sent: 0)" -ForegroundColor Red
Write-Host "  Timeout: ~21 seconds after request initiation" -ForegroundColor Gray
Write-Host ""

# Solution 1: Check VPN/TAP adapter interference
Write-Host "Solution 1: Check VPN/TAP Adapter Interference" -ForegroundColor Green
$tapAdapters = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like "*TAP*" -or $_.InterfaceDescription -like "*OpenVPN*" }
if ($tapAdapters) {
    Write-Host "  ⚠ Found VPN/TAP adapters (may interfere with SSL):" -ForegroundColor Yellow
    $tapAdapters | ForEach-Object { 
        Write-Host "    - $($_.Name): $($_.InterfaceDescription) [Status: $($_.Status)]" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "  RECOMMENDED: Temporarily disable VPN/TAP adapters and test Darktide" -ForegroundColor Yellow
    Write-Host "  To disable: Disable-NetAdapter -Name `"$($tapAdapters[0].Name)`" -Confirm:`$false" -ForegroundColor Gray
} else {
    Write-Host "  ✓ No VPN/TAP adapters detected" -ForegroundColor Green
}
Write-Host ""

# Solution 2: Check Windows Firewall rules for Darktide
Write-Host "Solution 2: Check Windows Firewall Rules" -ForegroundColor Green
$darktidePath = "D:\SteamLibrary\steamapps\common\Warhammer 40,000 DARKTIDE\binaries\Darktide.exe"
if (Test-Path $darktidePath) {
    $firewallRules = Get-NetFirewallApplicationFilter | Where-Object { $_.Program -like "*Darktide*" }
    if ($firewallRules) {
        Write-Host "  Found firewall rules for Darktide:" -ForegroundColor Gray
        $firewallRules | ForEach-Object {
            $rule = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*Darktide*" }
            if ($rule) {
                Write-Host "    - $($rule.DisplayName): $($rule.Action)" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  ⚠ No specific firewall rules found for Darktide" -ForegroundColor Yellow
        Write-Host "  Consider adding an exception for Darktide.exe" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠ Darktide.exe not found at expected path" -ForegroundColor Yellow
}
Write-Host ""

# Solution 3: Check schannel timeout settings
Write-Host "Solution 3: Check Windows schannel Timeout Settings" -ForegroundColor Green
$schannelPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL"
$timeoutSettings = @(
    "ClientCacheTime",
    "ServerCacheTime"
)

foreach ($setting in $timeoutSettings) {
    $value = Get-ItemProperty -Path $schannelPath -Name $setting -ErrorAction SilentlyContinue
    if ($value) {
        Write-Host "  $setting = $($value.$setting)" -ForegroundColor Gray
    } else {
        Write-Host "  $setting = (default)" -ForegroundColor Gray
    }
}
Write-Host ""

# Solution 4: Test DNS resolution
Write-Host "Solution 4: Test DNS Resolution" -ForegroundColor Green
$targetHost = "bsp-sup-sd.atoma-discovery.com"
try {
    $dnsResult = Resolve-DnsName -Name $targetHost -ErrorAction Stop
    Write-Host "  ✓ DNS resolution successful:" -ForegroundColor Green
    $dnsResult | Select-Object -First 3 | ForEach-Object {
        Write-Host "    - $($_.IPAddress)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ✗ DNS resolution failed: $_" -ForegroundColor Red
}
Write-Host ""

# Solution 5: Test SSL/TLS connection
Write-Host "Solution 5: Test SSL/TLS Connection" -ForegroundColor Green
$testUrl = "https://bsp-sup-sd.atoma-discovery.com/bishop/steam_1361210_default"
try {
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-WebRequest -Uri $testUrl -UseBasicParsing -TimeoutSec 30 -ErrorAction Stop
    $stopwatch.Stop()
    Write-Host "  ✓ Connection successful (Status: $($response.StatusCode), Time: $($stopwatch.ElapsedMilliseconds)ms)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Connection failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Message -like "*timeout*") {
        Write-Host "  ⚠ This confirms a timeout issue" -ForegroundColor Yellow
    }
}
Write-Host ""

# Solution 6: Check network adapter priority
Write-Host "Solution 6: Check Network Adapter Priority" -ForegroundColor Green
$adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Sort-Object InterfaceMetric
Write-Host "  Active network adapters (by priority):" -ForegroundColor Gray
$adapters | ForEach-Object {
    Write-Host "    $($_.InterfaceMetric) - $($_.Name): $($_.InterfaceDescription)" -ForegroundColor Gray
}
Write-Host ""

# Solution 7: Check for proxy settings
Write-Host "Solution 7: Check Proxy Settings" -ForegroundColor Green
$proxy = netsh winhttp show proxy
if ($proxy -like "*proxy*" -and $proxy -notlike "*Direct access*") {
    Write-Host "  ⚠ Proxy detected - may interfere with SSL:" -ForegroundColor Yellow
    Write-Host "  $proxy" -ForegroundColor Gray
    Write-Host "  Consider disabling proxy for Darktide" -ForegroundColor Gray
} else {
    Write-Host "  ✓ No proxy configured" -ForegroundColor Green
}
Write-Host ""

# Solution 8: Check TCP/IP settings
Write-Host "Solution 8: Check TCP/IP Settings" -ForegroundColor Green
$tcpTimedWaitDelay = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" -Name "TcpTimedWaitDelay" -ErrorAction SilentlyContinue
if ($tcpTimedWaitDelay) {
    Write-Host "  TcpTimedWaitDelay = $($tcpTimedWaitDelay.TcpTimedWaitDelay) seconds" -ForegroundColor Gray
} else {
    Write-Host "  TcpTimedWaitDelay = (default: 120 seconds)" -ForegroundColor Gray
}
Write-Host ""

# Solution 9: Check for antivirus/security software
Write-Host "Solution 9: Check for SSL Interception Software" -ForegroundColor Green
$securityProcesses = Get-Process | Where-Object { 
    $_.ProcessName -like "*kaspersky*" -or 
    $_.ProcessName -like "*norton*" -or 
    $_.ProcessName -like "*mcafee*" -or 
    $_.ProcessName -like "*avast*" -or 
    $_.ProcessName -like "*avg*" -or
    $_.ProcessName -like "*bitdefender*"
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

# Summary and recommendations
Write-Host "=== Summary and Recommendations ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Primary Issue: SSL/TLS handshake timeout - 21 seconds" -ForegroundColor Yellow
Write-Host ""
Write-Host "Most Likely Causes (in order):" -ForegroundColor Yellow
Write-Host "  1. VPN/TAP adapter interference (TAP-Windows Adapter detected)" -ForegroundColor White
Write-Host "  2. Firewall blocking SSL handshake" -ForegroundColor White
Write-Host "  3. Antivirus SSL interception" -ForegroundColor White
Write-Host "  4. Network adapter priority issues" -ForegroundColor White
Write-Host ""
Write-Host "Recommended Actions:" -ForegroundColor Yellow
Write-Host "  1. DISABLE VPN/TAP adapter temporarily and test" -ForegroundColor White
Write-Host "  2. Add Darktide.exe to Windows Firewall exceptions" -ForegroundColor White
Write-Host "  3. Check antivirus settings for SSL scanning" -ForegroundColor White
Write-Host "  4. Ensure Wi-Fi adapter has highest priority" -ForegroundColor White
Write-Host ""
Write-Host "Quick Test Commands:" -ForegroundColor Yellow
Write-Host "  # Disable TAP adapter:" -ForegroundColor Gray
Write-Host "  Disable-NetAdapter -Name `"TAP-Windows Adapter V9`" -Confirm:`$false" -ForegroundColor Gray
Write-Host ""
Write-Host "  # Add firewall exception:" -ForegroundColor Gray
Write-Host "  New-NetFirewallRule -DisplayName `"Darktide`" -Direction Outbound -Program `"$darktidePath`" -Action Allow" -ForegroundColor Gray
Write-Host ""

