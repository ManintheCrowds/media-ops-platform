# API Endpoints and Scheduler Audit - Easy Wins for Improvement

## Executive Summary

This audit identifies quick wins and improvements for the API endpoints and scheduler implementation. Issues are categorized by priority and effort required.

## Critical Issues (High Priority, Low Effort)

### 1. Scheduler: Broken Task Management
**File**: `app/api/scheduler.py`  
**Issue**: `_scheduler_task` is declared but never assigned, making the cancellation logic in `stop_scheduler()` ineffective.

**Current Code (lines 98-103)**:
```python
if _scheduler_task and not _scheduler_task.done():
    _scheduler_task.cancel()
    # This will never execute because _scheduler_task is always None
```

**Fix**: Remove unused `_scheduler_task` logic or properly implement async task tracking.

**Impact**: Medium - Scheduler stop may not properly cancel background tasks.

---

### 2. Missing Response Models
**File**: `app/api/scheduler.py`  
**Issue**: Endpoints don't use Pydantic response models, inconsistent with `services.py` pattern.

**Current**: Returns plain dicts  
**Expected**: Use `response_model` parameter like other endpoints

**Fix**: Create `SchedulerStatusResponse` and `SchedulerStartResponse` models.

**Impact**: Low - Affects API documentation and type safety.

---

### 3. Missing Status Endpoint
**File**: `app/api/scheduler.py`  
**Issue**: No way to check scheduler status without starting/stopping it.

**Fix**: Add `GET /api/v1/scheduler/status` endpoint.

**Impact**: Medium - Users can't query current state.

---

## High Priority Improvements

### 4. Input Validation Missing
**File**: `app/api/scheduler.py`  
**Issue**: No validation on:
- `min_match_score` (should be 0.0-1.0)
- `limit_per_query` (should be > 0, reasonable max)
- `location` (should not be empty)
- `queries` (should not be empty list if provided)

**Fix**: Add Pydantic validators to `ScheduledSearchRequest`.

**Impact**: Medium - Invalid inputs could cause runtime errors.

---

### 5. Thread Safety Issue
**File**: `app/api/scheduler.py`  
**Issue**: Global variables `_scheduler_running` and `_scheduler_task` accessed without locks in async context.

**Fix**: Use `asyncio.Lock()` or thread-safe state management.

**Impact**: Medium - Race conditions possible in concurrent requests.

---

### 6. Inconsistent Status Codes
**File**: `app/api/scheduler.py`  
**Issue**: Idempotent operations return 200, but should use appropriate status codes:
- Start when running: Could be 200 (current) or 409 Conflict
- Stop when not running: Could be 200 (current) or 404 Not Found

**Fix**: Use explicit status codes for clarity.

**Impact**: Low - Current behavior works but could be clearer.

---

## Medium Priority Improvements

### 7. Missing Error Response Models
**File**: `app/api/scheduler.py`  
**Issue**: Error responses not documented in OpenAPI schema.

**Fix**: Use `responses` parameter in route decorator to document error codes.

**Impact**: Low - Improves API documentation.

---

### 8. Background Task Not Actually Functional
**File**: `app/api/scheduler.py`  
**Issue**: `_scheduler_worker()` function does nothing (just `pass`).

**Fix**: Either remove placeholder or implement actual scheduler logic.

**Impact**: Medium - Feature doesn't actually work as expected.

---

### 9. Missing Request/Response Examples
**File**: `app/api/scheduler.py`  
**Issue**: Docstrings don't include example requests/responses.

**Fix**: Add examples to docstrings or use `example` in Pydantic models.

**Impact**: Low - Improves developer experience.

---

### 10. Inconsistent Error Handling
**File**: `app/api/scheduler.py`  
**Issue**: Error messages don't follow consistent pattern with other endpoints.

**Comparison**:
- `services.py`: Uses `status.HTTP_*` constants
- `scheduler.py`: Uses raw status codes (500)

**Fix**: Import and use `status` from `fastapi`.

**Impact**: Low - Code consistency.

---

## Low Priority / Nice to Have

### 11. Missing Admin-Only Protection
**File**: `app/api/scheduler.py`  
**Issue**: Scheduler endpoints don't check if user is admin (unlike service management).

**Fix**: Add admin check if scheduler should be admin-only.

**Impact**: Low - Depends on requirements.

---

### 12. No Rate Limiting
**File**: `app/api/scheduler.py`  
**Issue**: No rate limiting on scheduler start/stop endpoints.

**Fix**: Add Flask-Limiter or similar if needed.

**Impact**: Low - May not be necessary.

---

### 13. Missing Logging Context
**File**: `app/api/scheduler.py`  
**Issue**: Logs don't include user context or request IDs.

**Fix**: Add structured logging with user info.

**Impact**: Low - Improves debugging.

---

## API Consistency Issues

### 14. Response Model Pattern Inconsistency
**Files**: All API files  
**Issue**: 
- `services.py`: Uses `response_model` consistently
- `scheduler.py`: Returns dicts directly
- `health.py`: Mix of both

**Fix**: Standardize on response models for all endpoints.

**Impact**: Medium - Affects maintainability and type safety.

---

### 15. Missing OpenAPI Tags Organization
**Files**: All API files  
**Issue**: Tags are defined but could be better organized.

**Fix**: Ensure consistent tag naming and grouping.

**Impact**: Low - Documentation organization.

---

## Recommended Implementation Order

### Phase 1: Critical Fixes (1-2 hours)
1. Fix broken task management (#1)
2. Add input validation (#4)
3. Add status endpoint (#3)

### Phase 2: Consistency (1-2 hours)
4. Add response models (#2)
5. Fix status codes (#6)
6. Standardize error handling (#10)

### Phase 3: Polish (1 hour)
7. Add error response documentation (#7)
8. Add request/response examples (#9)
9. Improve logging (#13)

### Phase 4: Future Enhancements
10. Thread safety improvements (#5)
11. Implement actual scheduler logic (#8)
12. Admin-only protection if needed (#11)

---

## Code Examples for Quick Fixes

### Fix #1: Remove Broken Task Logic
```python
# Remove _scheduler_task entirely or properly implement:
# Option A: Remove it
_scheduler_running = False  # Remove _scheduler_task

# Option B: Properly track task
_scheduler_task: Optional[asyncio.Task] = None
# Then in start_scheduler:
_scheduler_task = asyncio.create_task(_scheduler_worker())
```

### Fix #2: Add Response Models
```python
class SchedulerStatusResponse(BaseModel):
    """Scheduler status response."""
    status: str  # "running" | "stopped"
    message: str
    location: Optional[str] = None
    min_match_score: Optional[float] = None
    queries: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    limit_per_query: Optional[int] = None

@router.post("/start", response_model=SchedulerStatusResponse)
```

### Fix #3: Add Status Endpoint
```python
@router.get("/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(
    current_user: User = Depends(get_current_user)
):
    """Get current scheduler status."""
    return {
        "status": "running" if _scheduler_running else "stopped",
        "message": "Scheduler is running" if _scheduler_running else "Scheduler is stopped"
    }
```

### Fix #4: Add Input Validation
```python
from pydantic import field_validator

class ScheduledSearchRequest(BaseModel):
    queries: Optional[List[str]] = None
    location: str = "Minneapolis, MN"
    sources: Optional[List[str]] = None
    min_match_score: float = 0.7
    limit_per_query: int = 10
    
    @field_validator('min_match_score')
    @classmethod
    def validate_match_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('min_match_score must be between 0.0 and 1.0')
        return v
    
    @field_validator('limit_per_query')
    @classmethod
    def validate_limit(cls, v):
        if v < 1 or v > 100:
            raise ValueError('limit_per_query must be between 1 and 100')
        return v
    
    @field_validator('location')
    @classmethod
    def validate_location(cls, v):
        if not v or not v.strip():
            raise ValueError('location cannot be empty')
        return v.strip()
```

---

## Summary

**Total Issues Identified**: 15  
**Critical**: 3  
**High Priority**: 3  
**Medium Priority**: 4  
**Low Priority**: 5  

**Estimated Total Fix Time**: 4-6 hours for all improvements  
**Quick Wins (Phase 1)**: 1-2 hours for critical fixes

The most impactful quick wins are:
1. Fixing the broken task management
2. Adding input validation
3. Adding a status endpoint
4. Adding response models for consistency

These changes will significantly improve the robustness, usability, and maintainability of the scheduler API.

