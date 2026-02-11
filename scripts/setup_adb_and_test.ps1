# PURPOSE: Locate platform-tools, add to PATH, and test ADB connection to S22
# DEPENDENCIES: platform-tools extracted somewhere on system
# MODIFICATION NOTES: Initial version for S22 data extraction setup

Write-Host "=== ADB Setup and Connection Test ===" -ForegroundColor Cyan

# Step 1: Locate platform-tools
Write-Host "`n[1/5] Locating platform-tools..." -ForegroundColor Yellow
$searchPaths = @(
    "C:\platform-tools",
    "D:\platform-tools", 
    "E:\platform-tools",
    "$env:USERPROFILE\Downloads\platform-tools",
    "$env:USERPROFILE\Desktop\platform-tools",
    "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Google.PlatformTools*\platform-tools"
)

$platformToolsPath = $null
foreach ($path in $searchPaths) {
    if (Test-Path "$path\adb.exe") {
        $platformToolsPath = (Resolve-Path $path).Path
        Write-Host "Found: $platformToolsPath" -ForegroundColor Green
        break
    }
}

# If not found, try recursive search
if (-not $platformToolsPath) {
    Write-Host "Searching recursively..." -ForegroundColor Yellow
    $found = Get-ChildItem -Path C:\,D:\,E:\,$env:USERPROFILE -Filter "adb.exe" -Recurse -ErrorAction SilentlyContinue -Depth 4 | Select-Object -First 1
    if ($found) {
        $platformToolsPath = Split-Path $found.FullName -Parent
        Write-Host "Found: $platformToolsPath" -ForegroundColor Green
    }
}

# If still not found, prompt user
if (-not $platformToolsPath) {
    Write-Host "Platform-tools not found automatically." -ForegroundColor Red
    $manualPath = Read-Host "Please enter the full path to platform-tools directory (e.g., C:\platform-tools)"
    if (Test-Path "$manualPath\adb.exe") {
        $platformToolsPath = (Resolve-Path $manualPath).Path
        Write-Host "Using: $platformToolsPath" -ForegroundColor Green
    } else {
        Write-Host "Error: adb.exe not found at $manualPath" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Add to PATH
Write-Host "`n[2/5] Adding to PATH..." -ForegroundColor Yellow
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$platformToolsPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$platformToolsPath", "User")
    Write-Host "Added to user PATH" -ForegroundColor Green
} else {
    Write-Host "Already in PATH" -ForegroundColor Green
}

# Refresh current session
$env:Path += ";$platformToolsPath"

# Step 3: Verify ADB works
Write-Host "`n[3/5] Verifying ADB installation..." -ForegroundColor Yellow
try {
    $adbVersion = & "$platformToolsPath\adb.exe" version 2>&1
    Write-Host $adbVersion -ForegroundColor Green
} catch {
    Write-Host "Error: ADB not working" -ForegroundColor Red
    exit 1
}

# Step 4: Test connection
Write-Host "`n[4/5] Testing device connection..." -ForegroundColor Yellow
Write-Host "Make sure USB debugging is enabled on the S22 and the phone is connected." -ForegroundColor Cyan
Write-Host "If you see 'unauthorized', approve the RSA key on the phone." -ForegroundColor Cyan
Start-Sleep -Seconds 2

$devices = & "$platformToolsPath\adb.exe" devices
Write-Host $devices

if ($devices -match "device\s+device$") {
    Write-Host "Device connected successfully!" -ForegroundColor Green
} elseif ($devices -match "unauthorized") {
    Write-Host "Device is unauthorized. Please approve the RSA key on the phone, then run:" -ForegroundColor Yellow
    Write-Host "  adb devices" -ForegroundColor White
} elseif ($devices -match "List of devices attached" -and $devices -notmatch "device") {
    Write-Host "No devices found. Check USB connection and USB debugging settings." -ForegroundColor Red
} else {
    Write-Host "Connection status unclear. Check output above." -ForegroundColor Yellow
}

# Step 5: Verify device model
Write-Host "`n[5/5] Verifying device model..." -ForegroundColor Yellow
try {
    $model = & "$platformToolsPath\adb.exe" shell getprop ro.product.model 2>&1
    if ($model -and $model -notmatch "error") {
        Write-Host "Device Model: $model" -ForegroundColor Green
        if ($model -match "SM-S9|SM-S22") {
            Write-Host "Confirmed: S22 device detected!" -ForegroundColor Green
        }
    } else {
        Write-Host "Could not retrieve device model. Device may not be authorized or connected." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error retrieving device model" -ForegroundColor Red
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "ADB path: $platformToolsPath" -ForegroundColor White
Write-Host "You can now use 'adb' commands directly." -ForegroundColor White
