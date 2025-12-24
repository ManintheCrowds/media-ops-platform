# Quick Network Security Check
# Fast analysis of current network state

Write-Host "=== Quick Network Security Check ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check devices on network
Write-Host "1. Network Devices:" -ForegroundColor Yellow
arp -a | Select-String "192.168.0" | ForEach-Object {
    if ($_ -match "(\d+\.\d+\.\d+\.\d+)\s+([a-fA-F0-9-]+)") {
        $ip = $matches[1]
        $mac = $matches[2]
        if ($ip -ne "192.168.0.255") {
            Write-Host "   $ip - $mac" -ForegroundColor White
        }
    }
}

Write-Host ""

# 2. Check suspicious external connections
Write-Host "2. Suspicious External Connections:" -ForegroundColor Yellow
$suspicious = Get-NetTCPConnection -ErrorAction SilentlyContinue | 
    Where-Object { 
        $_.LocalAddress -like "192.168.0.*" -and 
        $_.RemoteAddress -notlike "192.168.0.*" -and
        $_.State -eq "Established"
    } | 
    Group-Object RemoteAddress | 
    Sort-Object Count -Descending | 
    Select-Object -First 5

foreach ($conn in $suspicious) {
    $percentage = [math]::Round(($conn.Count / (Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object { $_.LocalAddress -like "192.168.0.*" -and $_.RemoteAddress -notlike "192.168.0.*" }).Count) * 100, 1)
    Write-Host "   $($conn.Name): $($conn.Count) connections ($percentage%)" -ForegroundColor $(if ($conn.Count -gt 50) { "Red" } else { "White" })
}

Write-Host ""

# 3. Check internal connections
Write-Host "3. Internal Network Connections:" -ForegroundColor Yellow
$internal = Get-NetTCPConnection -ErrorAction SilentlyContinue | 
    Where-Object { 
        $_.LocalAddress -like "192.168.0.*" -and 
        $_.RemoteAddress -like "192.168.0.*" -and
        $_.State -eq "Established"
    } | 
    Group-Object RemoteAddress

foreach ($conn in $internal) {
    $ports = ($conn.Group | Select-Object -Unique RemotePort) -join ", "
    Write-Host "   $($conn.Name): $($conn.Count) connections on ports $ports" -ForegroundColor White
}

Write-Host ""

# 4. Check for process making suspicious connections
Write-Host "4. Top Network-Active Processes:" -ForegroundColor Yellow
$processes = Get-NetTCPConnection -ErrorAction SilentlyContinue | 
    Where-Object { $_.State -eq "Established" -and $_.LocalAddress -like "192.168.0.*" } |
    Group-Object OwningProcess | 
    Sort-Object Count -Descending | 
    Select-Object -First 5

foreach ($proc in $processes) {
    try {
        $p = Get-Process -Id $proc.Name -ErrorAction SilentlyContinue
        if ($p) {
            Write-Host "   $($p.ProcessName): $($proc.Count) connections" -ForegroundColor White
        }
    } catch {}
}

Write-Host ""

# 5. Quick recommendations
Write-Host "5. Quick Actions:" -ForegroundColor Yellow
Write-Host "   [ ] Verify device at 192.168.0.43 is known" -ForegroundColor White
Write-Host "   [ ] Research 91.222.185.x IP range" -ForegroundColor White
Write-Host "   [ ] Check router admin panel for full device list" -ForegroundColor White
Write-Host "   [ ] Run full audit: .\scripts\security\network-audit-analysis.ps1" -ForegroundColor White

Write-Host ""
Write-Host "For detailed analysis, run:" -ForegroundColor Cyan
Write-Host "  .\scripts\security\network-audit-analysis.ps1" -ForegroundColor Green

