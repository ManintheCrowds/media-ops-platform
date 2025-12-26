# System Test Plan - Smart Execution with Checkpoints

## Current Status
- ✅ Database: Connected (242 jobs: 18 Adzuna, 224 legacy)
- ✅ API Credentials: All configured (Adzuna, JSearch)
- ✅ API Server: Running on port 8004
- ⚠️  Job Search: Endpoint works but returns 0 jobs (server needs restart to load credentials)
- ⚠️  Legacy Jobs: 224 jobs without source attribution

## Test Execution Plan

### Phase 1: Prerequisites (5 min)
**Status**: ✅ Complete
- [x] Database running (PostgreSQL on port 5433)
- [x] API credentials configured (.env file)
- [x] Dependencies installed
- [x] Server running (port 8004)

### Phase 2: Server Restart (2 min)
**Status**: ⚠️ Needed
**Action**: Restart server to load .env credentials
```powershell
cd d:\software\job-automation-service
.\restart_server.ps1
```

**Verification**:
```powershell
# Wait 5 seconds, then check
Invoke-RestMethod -Uri "http://localhost:8004/health"
python test_endpoint_detailed.py
```

**Checkpoint**: Save server status after restart

### Phase 3: Job Search Test (3 min)
**Status**: Pending
**Action**: Test job search with Adzuna
```powershell
$body = @{
    query='python developer'
    location='Minneapolis, MN'
    limit=10
    sources=@('adzuna')
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://localhost:8004/api/v1/jobs/search' -Method POST -Body $body -ContentType 'application/json'
```

**Expected**: Should return 5-10 jobs from Adzuna

**Checkpoint**: Save search results

### Phase 4: Database Verification (2 min)
**Status**: Pending
**Action**: Verify jobs saved to database
```powershell
python get_all_jobs.py | Select-Object -First 30
```

**Expected**: 
- New jobs should have `source="adzuna"`
- Jobs should have match scores > 0
- Jobs should have descriptions

**Checkpoint**: Save job count and sample jobs

### Phase 5: Source Attribution Test (2 min)
**Status**: Pending
**Action**: Verify source attribution works
```powershell
python -c "from app.database import SessionLocal; from app.models.job_listing import JobListing; db = SessionLocal(); print(f'Adzuna jobs: {db.query(JobListing).filter(JobListing.source == \"adzuna\").count()}')"
```

**Expected**: Adzuna job count should increase after search

### Phase 6: Match Score Verification (2 min)
**Status**: Pending
**Action**: Verify match scores are calculated
```powershell
python -c "from app.database import SessionLocal; from app.models.job_listing import JobListing; db = SessionLocal(); jobs = db.query(JobListing).filter(JobListing.source == 'adzuna', JobListing.overall_match_score > 0).limit(5).all(); [print(f'{j.title}: {j.overall_match_score}') for j in jobs]"
```

**Expected**: Jobs should have scores in 0.0-1.0 range

### Phase 7: Comprehensive Audit (5 min)
**Status**: Pending
**Action**: Run full audit suite
```powershell
python audit_run_all.py
```

**Expected**: All audit scripts pass, master report generated

**Checkpoint**: Save audit report location

## Quick Test Script

Run this to execute all phases with automatic checkpointing:

```powershell
cd d:\software\job-automation-service
python test_system_comprehensive.py
```

## Manual Step-by-Step

If you prefer manual execution, follow phases 2-7 above in order. Each phase can be run independently and results are saved to checkpoints.

## Recovery from Disconnect

If disconnected:
1. Check `test_checkpoint.json` for completed tests
2. Run `python test_system_comprehensive.py` - it will skip completed tests
3. Or manually continue from the last completed phase

## Success Criteria

- ✅ Server restarted and healthy
- ✅ Job search returns 5+ jobs from Adzuna
- ✅ Jobs saved to database with source="adzuna"
- ✅ Jobs have match scores calculated
- ✅ All audit tests pass
- ✅ Master audit report generated

