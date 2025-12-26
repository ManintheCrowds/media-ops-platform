# Kill ALL server processes and start fresh
# This ensures no old server instances are running

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "KILLING ALL SERVER PROCESSES" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Step 1: Find all processes using port 8004
Write-Host "[1/4] Finding processes on port 8004..." -ForegroundColor Yellow
$portProcesses = Get-NetTCPConnection -LocalPort 8004 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($portProcesses) {
    Write-Host "  Found $($portProcesses.Count) process(es) on port 8004" -ForegroundColor Yellow
    foreach ($processId in $portProcesses) {
        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "    PID $processId : $($proc.ProcessName) - $($proc.Path)" -ForegroundColor Cyan
        }
    }
} else {
    Write-Host "  No processes found on port 8004" -ForegroundColor Green
}

# Step 2: Find all Python processes that might be uvicorn servers
Write-Host ""
Write-Host "[2/4] Finding Python/uvicorn processes..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*" -or 
    $_.CommandLine -like "*app.main*" -or
    $_.Path -like "*Python313*"
} | Select-Object Id, ProcessName, Path, @{Name="CommandLine";Expression={(Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine}}

if ($pythonProcesses) {
    Write-Host "  Found $($pythonProcesses.Count) Python process(es)" -ForegroundColor Yellow
    foreach ($proc in $pythonProcesses) {
        $cmdLine = if ($proc.CommandLine) { $proc.CommandLine.Substring(0, [Math]::Min(80, $proc.CommandLine.Length)) } else { "N/A" }
        Write-Host "    PID $($proc.Id) : $cmdLine..." -ForegroundColor Cyan
    }
} else {
    Write-Host "  No Python processes found" -ForegroundColor Green
}

# Step 3: Kill all identified processes
Write-Host ""
Write-Host "[3/4] Killing all server processes..." -ForegroundColor Yellow
$allPids = @()
if ($portProcesses) { $allPids += $portProcesses }
if ($pythonProcesses) { $allPids += $pythonProcesses.Id }
$allPids = $allPids | Sort-Object -Unique

if ($allPids.Count -gt 0) {
    foreach ($processId in $allPids) {
        try {
            $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "  Killing PID $processId ($($proc.ProcessName))..." -ForegroundColor Yellow
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 200
            }
        } catch {
            Write-Host "    (Process $processId already terminated)" -ForegroundColor Gray
        }
    }
    Write-Host "  [OK] All processes killed" -ForegroundColor Green
} else {
    Write-Host "  [OK] No processes to kill" -ForegroundColor Green
}

# Step 4: Verify port is free
Write-Host ""
Write-Host "[4/4] Verifying port 8004 is free..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
$remaining = Get-NetTCPConnection -LocalPort 8004 -ErrorAction SilentlyContinue
if ($remaining) {
    Write-Host "  [WARN] Port still in use, force killing..." -ForegroundColor Yellow
    $remainingPids = $remaining | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $remainingPids) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
} else {
    Write-Host "  [OK] Port 8004 is free" -ForegroundColor Green
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "ALL SERVER PROCESSES TERMINATED" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

