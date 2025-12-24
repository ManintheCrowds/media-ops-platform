# Quick Testing Guide - Scheduler Endpoints

## Immediate Action Required

**The server must be restarted for the scheduler endpoints to work.**

### Step 1: Restart Server

**Option A: Use the restart script**
```powershell
.\restart_server.ps1
```

**Option B: Manual restart**
1. Stop current server: Press `Ctrl+C` in the uvicorn terminal
2. Start server:
   ```powershell
   $env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
   ```

### Step 2: Verify Routes Are Registered

```powershell
python check_openapi.py
```

**Expected output:**
```
Scheduler routes in OpenAPI schema:
[
  "/api/v1/scheduler/daily",
  "/api/v1/scheduler/search",
  "/api/v1/scheduler/start",    ← Should appear
  "/api/v1/scheduler/stop",    ← Should appear
  "/api/v1/scheduler/weekly"
]

Start/Stop routes found: 2
  /api/v1/scheduler/start
  /api/v1/scheduler/stop
```

### Step 3: Test Endpoints

```powershell
python test_endpoints.py
```

**Expected output:**
```
POST /api/v1/scheduler/start: 200  ← Should be 200, not 404
POST /api/v1/scheduler/stop: 200   ← Should be 200, not 404
POST /api/v1/scheduler/search: 200
```

### Step 4: Run Agent Tests

```powershell
$env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"
python -m tests.agents.run_agents --suite full
```

The scheduler test agent should now pass.

## Troubleshooting

**If routes still don't appear after restart:**

1. Verify code is correct:
   ```powershell
   python test_route_registration.py
   ```
   Should show 5 scheduler routes including start/stop

2. Check server logs for import errors

3. Verify you're in the correct directory:
   ```powershell
   pwd  # Should be: C:\Users\artin\software\job-automation-service
   ```

4. Try a fresh start:
   - Stop server completely
   - Clear cache again: Remove all `__pycache__` directories
   - Restart server

## Test Endpoints Manually

**Using PowerShell:**
```powershell
# Test start endpoint
Invoke-WebRequest -Uri "http://localhost:8004/api/v1/scheduler/start" `
  -Method POST -ContentType "application/json" -Body '{}'

# Test stop endpoint  
Invoke-WebRequest -Uri "http://localhost:8004/api/v1/scheduler/stop" `
  -Method POST -ContentType "application/json"
```

**Using curl (if available):**
```bash
curl -X POST http://localhost:8004/api/v1/scheduler/start \
  -H "Content-Type: application/json" \
  -d '{}'

curl -X POST http://localhost:8004/api/v1/scheduler/stop \
  -H "Content-Type: application/json"
```

## Files Created

- `test_route_registration.py` - Check route registration
- `test_endpoints.py` - Test all endpoints
- `check_openapi.py` - Verify OpenAPI schema
- `restart_server.ps1` - Helper script to restart server
- `TESTING_RESULTS.md` - Detailed test results
- `QUICK_TEST_GUIDE.md` - This file

