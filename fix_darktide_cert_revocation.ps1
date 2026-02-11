# PURPOSE: Fix Darktide certificate revocation error (CRYPT_E_REVOCATION_OFFLINE)
# DEPENDENCIES: Windows PowerShell (Run as Administrator)
# MODIFICATION NOTES: Created to troubleshoot Darktide backend authentication errors

Write-Host "=== Darktide Certificate Revocation Fix ===" -ForegroundColor Cyan
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator. Some fixes may not work." -ForegroundColor Yellow
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
}

# Solution 1: Disable certificate revocation checking for current user (RECOMMENDED)
Write-Host "Solution 1: Disable certificate revocation check (Current User)" -ForegroundColor Green
$userPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\WinTrust\Trust Providers\Software Publishing"
$statePath = "$userPath\State"

try {
    if (-not (Test-Path $userPath)) {
        New-Item -Path $userPath -Force | Out-Null
    }
    if (-not (Test-Path $statePath)) {
        New-Item -Path $statePath -Force | Out-Null
    }
    
    $currentState = Get-ItemProperty -Path $statePath -Name "State" -ErrorAction SilentlyContinue
    if ($currentState.State -ne 0x23C00) {
        Set-ItemProperty -Path $statePath -Name "State" -Value 0x23C00 -Type DWord
        Write-Host "  ✓ Disabled certificate revocation checking for current user" -ForegroundColor Green
        Write-Host "  State set to 0x23C00 (disables revocation check)" -ForegroundColor Gray
    } else {
        Write-Host "  ✓ Certificate revocation checking already disabled for current user" -ForegroundColor Green
    }
} catch {
    Write-Host "  ✗ Failed to set user registry: $_" -ForegroundColor Red
}

Write-Host ""

# Solution 2: Check Internet Options certificate revocation
Write-Host "Solution 2: Check Internet Options Certificate Settings" -ForegroundColor Green
$internetOptionsPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
$certRevokeFlags = Get-ItemProperty -Path $internetOptionsPath -Name "CertificateRevocation" -ErrorAction SilentlyContinue

if ($certRevokeFlags) {
    Write-Host "  Current CertificateRevocation value: $($certRevokeFlags.CertificateRevocation)" -ForegroundColor Gray
    if ($certRevokeFlags.CertificateRevocation -ne 0) {
        Write-Host "  ⚠ Certificate revocation is enabled in Internet Options" -ForegroundColor Yellow
        Write-Host "  To disable: Internet Options > Advanced > Security > Uncheck 'Check for server certificate revocation'" -ForegroundColor Gray
    }
} else {
    Write-Host "  ✓ CertificateRevocation not explicitly set (using defaults)" -ForegroundColor Green
}

Write-Host ""

# Solution 3: Check for VPN/Proxy interference
Write-Host "Solution 3: Check Network Configuration" -ForegroundColor Green
$vpnAdapters = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like "*TAP*" -or $_.InterfaceDescription -like "*OpenVPN*" }
if ($vpnAdapters) {
    Write-Host "  ⚠ Found VPN/TAP adapters:" -ForegroundColor Yellow
    $vpnAdapters | ForEach-Object { Write-Host "    - $($_.Name): $($_.InterfaceDescription)" -ForegroundColor Gray }
    Write-Host "  Consider temporarily disabling VPN to test" -ForegroundColor Gray
} else {
    Write-Host "  ✓ No VPN/TAP adapters detected" -ForegroundColor Green
}

$proxy = netsh winhttp show proxy
if ($proxy -like "*proxy*") {
    Write-Host "  ⚠ Proxy detected - may interfere with certificate checks" -ForegroundColor Yellow
    Write-Host "  $proxy" -ForegroundColor Gray
} else {
    Write-Host "  ✓ No proxy configured" -ForegroundColor Green
}

Write-Host ""

# Solution 4: Test certificate revocation server connectivity
Write-Host "Solution 4: Test Certificate Revocation Server Connectivity" -ForegroundColor Green
$ocspServers = @(
    "ocsp.digicert.com",
    "ocsp.verisign.com",
    "ocsp.globalsign.com"
)

foreach ($server in $ocspServers) {
    $test = Test-NetConnection -ComputerName $server -Port 80 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($test) {
        Write-Host "  ✓ Can reach $server" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Cannot reach $server" -ForegroundColor Red
    }
}

Write-Host ""

# Solution 5: Check Windows Certificate Store
Write-Host "Solution 5: Check Certificate Store" -ForegroundColor Green
$certCount = (Get-ChildItem -Path Cert:\CurrentUser\TrustedPublisher | Measure-Object).Count
Write-Host "  Trusted Publishers: $certCount certificates" -ForegroundColor Gray

$certCount = (Get-ChildItem -Path Cert:\CurrentUser\Root | Measure-Object).Count
Write-Host "  Trusted Root CAs: $certCount certificates" -ForegroundColor Gray

Write-Host ""

# Solution 6: Check Windows Time Sync
Write-Host "Solution 6: Check System Time" -ForegroundColor Green
$timeSync = (Get-Service -Name "W32Time" -ErrorAction SilentlyContinue).Status
if ($timeSync -eq "Running") {
    Write-Host "  ✓ Windows Time service is running" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Windows Time service is not running" -ForegroundColor Yellow
    Write-Host "  Certificate validation requires accurate system time" -ForegroundColor Gray
}

$currentTime = Get-Date
Write-Host "  Current system time: $currentTime" -ForegroundColor Gray

Write-Host ""

# Summary and next steps
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Primary Fix Applied:" -ForegroundColor Yellow
Write-Host "  - Disabled certificate revocation checking for current user (State = 0x23C00)" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Restart Darktide and try logging in again" -ForegroundColor White
Write-Host "  2. If issue persists, try Solution 2 (Internet Options)" -ForegroundColor White
Write-Host "  3. If using VPN, try disabling it temporarily" -ForegroundColor White
Write-Host "  4. Check Windows Firewall isn't blocking certificate revocation servers" -ForegroundColor White
Write-Host ""
Write-Host "To Revert (re-enable revocation checking):" -ForegroundColor Yellow
Write-Host "  Remove-ItemProperty -Path `"$statePath`" -Name 'State' -ErrorAction SilentlyContinue" -ForegroundColor Gray
Write-Host ""

# Test the fix
Write-Host "Testing connection to Darktide backend..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "https://bsp-sup-sd.atoma-discovery.com/bishop/steam_1361210_default" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host "  ✓ Successfully connected to backend (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Connection failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  This may be expected if authentication is required" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Done! Restart Darktide and try again." -ForegroundColor Cyan

