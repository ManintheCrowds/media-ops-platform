# Next Steps to Get Server Returning Jobs

## Current Status
- ✅ Direct Python test works: Returns 3 jobs from Adzuna
- ✅ Code is correct: JobSourceManager works when tested directly
- ⚠️ Server endpoint returns 0 jobs
- ⚠️ Server process likely doesn't have credentials loaded

## Critical: Check Server Console Window

**The server window should be visible now.** Look for this section:

```
================================================================================
SERVER STARTUP - CREDENTIALS CHECK
================================================================================
Working Directory: D:\software\job-automation-service
Env File Path: D:\software\job-automation-service\.env
Env File Exists: True/False
Adzuna API ID: a4a7673a
Adzuna API Key: Set/NOT SET
JSearch API Key: Set/NOT SET
Has Adzuna Client: True/False
================================================================================
```

### If "Has Adzuna Client: False"
**This is the problem!** The server doesn't have credentials.

### If "Has Adzuna Client: True"
But still returns 0 jobs, then check for:
- `[DEBUG] Calling source_manager.search_jobs with sources: ['adzuna']`
- `[DEBUG] source_manager.search_jobs returned X jobs`
- `[ENDPOINT ERROR]` messages

## Solution Options

### Option 1: Manual Server Start with Explicit Env Vars (RECOMMENDED)

1. **Stop the current server** (Ctrl+C in server window)

2. **Start server manually with explicit environment variables:**
```powershell
cd D:\software\job-automation-service

# Set environment variables
$env:ADZUNA_API_ID = "a4a7673a"
$env:ADZUNA_API_KEY = "f6163b196847b9d597b71b9df86fdd2d"
$env:JSEARCH_API_KEY = "ak_r2baolkzsanqqwhfditlmydwa9jtcyei2qynhxqmqfdvvw4"
$env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"

# Start server
C:\Python313\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

3. **Watch the startup messages** - should show "Has Adzuna Client: True"

4. **Test the endpoint:**
```powershell
$body = @{query="python"; location="Minneapolis, MN"; limit=5; sources=@("adzuna")} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8004/api/v1/jobs/search" -Method POST -Body $body -ContentType "application/json"
```

### Option 2: Use the Fix Script

```powershell
cd D:\software\job-automation-service
.\fix_server_credentials.ps1
```

This script:
- Stops existing server
- Sets environment variables
- Starts server with explicit credentials
- Tests the endpoint

### Option 3: Check What Server Sees

If the server shows "Has Adzuna Client: False" in startup, the issue is credential loading.

**Verify .env file is accessible:**
```powershell
cd D:\software\job-automation-service
Test-Path .env
Get-Content .env | Select-Object -First 5
```

**Test credentials work:**
```powershell
python test_server_env_loading.py
```
This should return 3 jobs, proving credentials work.

## Expected Behavior After Fix

Once credentials are loaded correctly:

1. **Server startup shows:**
   - `Has Adzuna Client: True`
   - `SUCCESS: All credentials loaded correctly`

2. **Endpoint returns jobs:**
   ```powershell
   $body = @{query="python"; location="Minneapolis, MN"; limit=5; sources=@("adzuna")} | ConvertTo-Json
   Invoke-RestMethod -Uri "http://localhost:8004/api/v1/jobs/search" -Method POST -Body $body -ContentType "application/json"
   ```
   Should return 5+ jobs with:
   - `count > 0`
   - `jobs` array populated
   - Jobs have `source="adzuna"`

3. **Server console shows:**
   - `[DEBUG] source_manager.search_jobs returned X jobs` (where X > 0)

## Debugging Checklist

- [ ] Check server console window for startup messages
- [ ] Verify "Has Adzuna Client: True" in startup
- [ ] If False, check .env file exists and is readable
- [ ] Test credentials directly: `python test_server_env_loading.py`
- [ ] Restart server with explicit environment variables
- [ ] Call endpoint and watch for [DEBUG] messages
- [ ] Check for [ENDPOINT ERROR] messages

## Key Insight

The code works perfectly (direct test returns 3 jobs). The issue is **environment/process configuration**, not code bugs. Once the server process has the credentials, it will work immediately.

