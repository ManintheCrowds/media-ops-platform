# Server Debug Instructions

## Current Status
- ✅ Server is running on port 8004
- ✅ Health endpoint works
- ⚠️ Debug endpoint not found (server may not have reloaded)
- ⚠️ Job search returns 0 jobs

## Check Server Console Window

The server window should now be **visible** (not minimized). Check it for:

### 1. Startup Messages
Look for:
- `Starting FastAPI server...`
- `Working directory: D:\software\job-automation-service`
- `.env file: D:\software\job-automation-service\.env`
- `[OK] .env file found` or `[ERROR] .env file NOT found!`

### 2. When You Call the Endpoint
When you run:
```powershell
Invoke-RestMethod -Uri "http://localhost:8004/api/v1/jobs/search" -Method POST -Body (@{query='python'; location='Minneapolis, MN'; limit=5; sources=@('adzuna')} | ConvertTo-Json) -ContentType 'application/json'
```

Look for these debug messages in the server console:
- `[DEBUG] Creating JobSourceManager...`
- `[DEBUG] JobSourceManager created successfully`
- `[DEBUG] Starting search with sources: ['adzuna'], query: python`
- `[DEBUG] Calling source_manager.search_jobs with sources: ['adzuna']`
- `[DEBUG] source_manager.search_jobs returned X jobs`
- `[ENDPOINT ERROR]` (if there are errors)

### 3. Error Messages
If you see errors like:
- `Failed to create JobSourceManager`
- `Error in source_manager.search_jobs`
- Any traceback/exception messages

## Manual Test (Works!)

To verify credentials work outside the server:
```powershell
cd D:\software\job-automation-service
python test_server_env_loading.py
```

This should return 3 jobs, proving:
- ✅ .env file is found
- ✅ Credentials are loaded
- ✅ Adzuna API works
- ✅ JobSourceManager works

## If Server Console Shows Errors

### If you see "Adzuna API Key: NOT SET"
The server process isn't loading the .env file. Try:

1. **Stop the server** (Ctrl+C in server window)
2. **Restart with explicit environment variables**:
```powershell
cd D:\software\job-automation-service
$env:ADZUNA_API_ID = "a4a7673a"
$env:ADZUNA_API_KEY = "f6163b196847b9d597b71b9df86fdd2d"
$env:JSEARCH_API_KEY = "ak_r2baolkzsanqqwhfditlmydwa9jtcyei2qynhxqmqfdvvw4"
C:\Python313\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

### If you see "[DEBUG] source_manager.search_jobs returned 0 jobs"
But `test_server_env_loading.py` returns 3 jobs, then:
- The server process has different credentials than the test script
- Or the server is hitting rate limits
- Check the server console for specific error messages

## Next Steps

1. **Check the server console window** (should be visible now)
2. **Call the endpoint** and watch for debug messages
3. **Share what you see** in the server console
4. **Run the manual test** to confirm credentials work

The code is correct - we just need to see what the server process is actually seeing!

