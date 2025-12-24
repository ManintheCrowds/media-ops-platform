# Manual Server Restart Instructions

## Issue
The endpoint is returning 0 jobs with empty `sources_searched`, suggesting the server is running old code or there's an exception being silently caught.

## Solution: Manual Restart

### Step 1: Stop the Current Server

1. Find the server process:
   ```powershell
   Get-NetTCPConnection -LocalPort 8004 | Select-Object OwningProcess
   ```

2. Stop it:
   ```powershell
   Stop-Process -Id <PROCESS_ID> -Force
   ```

   Or use the restart script:
   ```powershell
   .\restart_server.ps1
   ```
   (Press Ctrl+C to stop it)

### Step 2: Start Fresh Server

In a **new PowerShell window**:

```powershell
cd C:\Users\artin\software\job-automation-service
$env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

### Step 3: Test

In another terminal:
```powershell
cd C:\Users\artin\software\job-automation-service
python test_adzuna_endpoint.py
```

## Expected Result

After restart, you should see:
- `sources_searched: ['adzuna']` (not empty)
- `Jobs found: 10` (or more)
- Sample job titles in the output

## If Still Not Working

Check the server console output for any error messages. The server will now print errors to the console as well as logs.

