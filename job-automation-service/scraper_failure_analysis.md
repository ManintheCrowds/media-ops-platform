# Scraper Failure Analysis

**Date**: December 23, 2025  
**Status**: Analysis Complete

## Executive Summary

All three major job site scrapers (Indeed, Glassdoor, ZipRecruiter) are currently blocked with 403 Forbidden errors due to anti-bot detection. While some anti-bot evasion features are implemented, they are not fully effective or not being used correctly.

## Failing Scrapers

| Scraper | Status | HTTP Code | Error Type | Response Time |
|---------|--------|-----------|------------|---------------|
| Indeed | ❌ Blocked | 403 | HTTPStatusError | 0.34s |
| Glassdoor | ❌ Blocked | 403 | HTTPStatusError | 0.66s |
| ZipRecruiter | ❌ Blocked | 403 | HTTPStatusError | 0.27s |

**Success Rate**: 0% (all requests blocked immediately)

## Current Evasion Strategies (What's Implemented)

### ✅ Enhanced HTTP Headers
- **Location**: `app/services/job_scraper.py:_get_enhanced_headers()`
- **Features**:
  - User-Agent rotation (5 different agents)
  - Accept-Language variations (4 variations)
  - Sec-Fetch headers (Dest, Mode, Site, User)
  - Referer chain support (code exists)
  - DNT and Upgrade-Insecure-Requests headers
- **Status**: ✅ Implemented and working

### ✅ User Agent Rotation
- **Location**: `app/services/job_scraper.py:USER_AGENTS`
- **Pool Size**: 5 realistic user agents (Chrome, Firefox, Safari on Windows/Mac/Linux)
- **Status**: ✅ Implemented

### ✅ Cookie Persistence Support
- **Location**: `app/services/job_scraper.py:_cookies` dict and `_fetch_page()`
- **Code Exists**: Lines 45, 140-141, 155-157
- **Status**: ⚠️ Code exists but cookies dict is always empty (not being populated)

### ✅ Browser Scraper (Playwright)
- **Location**: `app/services/browser_scraper.py`
- **Features**:
  - Playwright-based browser automation
  - Stealth mode support
  - JavaScript execution
- **Status**: ✅ Implemented but not used as fallback

### ✅ Rate Limiting
- **Location**: `app/utils/rate_limiter.py`
- **Features**:
  - Time-based multipliers
  - Human-like delays
  - Exponential backoff support
- **Status**: ✅ Implemented but not integrated into HTTP scrapers

## Gaps Identified

### ❌ Cookie Persistence Not Active
**Issue**: Cookie dict exists but is never populated from responses

**Current Code** (lines 155-157):
```python
if getattr(settings, 'cookie_persistence', True):
    for cookie in response.cookies.jar:
        self._cookies[cookie.name] = cookie.value
```

**Problem**: 
- `response.cookies.jar` may not be the correct way to access cookies in httpx
- Cookies are never reused in subsequent requests (only added to kwargs if dict is non-empty)
- No cookie persistence across scraper instances

**Impact**: High - Missing session cookies is a major anti-bot detection signal

---

### ❌ Human-like Delays Not Implemented in HTTP Scrapers
**Issue**: Rate limiter has human delay logic, but HTTP scrapers don't use it

**Current Code**: 
- `RateLimiter` has `_calculate_human_delay()` method
- `BaseJobScraper._fetch_page()` calls `await self.rate_limiter.wait()`
- But `wait()` uses `_calculate_human_delay()` only if `use_human_delays` is True

**Problem**:
- Delays are applied via rate limiter, but may not be sufficient
- No additional delays before requests (only between requests)
- No reading pauses integrated into request flow

**Impact**: Medium - Human-like timing is important for anti-bot evasion

---

### ❌ Browser Scraper Not Used as Fallback
**Issue**: When HTTP scraper gets 403, system doesn't try browser scraper

**Current Flow**: `JobSourceManager` → HTTP Scraper → Error (403)

**Missing**: HTTP Scraper → 403 → Browser Scraper → (retry)

**Impact**: High - Browser scraper exists but isn't being utilized when HTTP fails

---

### ❌ 403 Treated as Permanent Failure
**Issue**: When HTTP scraper gets 403, it immediately fails without retry

**Current Code** (job_scraper.py:190-242):
```python
except httpx.HTTPStatusError as e:
    if e.response.status_code == 403:
        # Treated as permanent failure - no retry
        return None
```

**Problem**:
- 403 errors don't trigger retry logic
- No exponential backoff on 403
- No user agent rotation on retry
- No browser scraper fallback

**Impact**: High - Immediate failure prevents any recovery attempts

---

### ❌ No Exponential Backoff with Jitter
**Issue**: Retry logic exists but doesn't use exponential backoff for 403 errors

**Current Code**: 
- Retry loop exists (lines 125-242)
- But 403 errors exit immediately
- No backoff delay for 403 retries

**Impact**: Medium - Rapid retries are a bot detection signal

---

### ❌ User Agent Not Rotated on Retry
**Issue**: User agent is set once per request, not rotated on retries

**Current Code**:
- User agent selected once in `_get_enhanced_headers()`
- Same user agent used for all retry attempts
- No rotation between retries

**Impact**: Medium - Rotating user agent on retry can help evade detection

---

## Recommendations (Prioritized)

### Priority 1: Activate Cookie Management (HIGH)
1. Fix cookie extraction from httpx responses
2. Ensure cookies are saved after each successful response
3. Reuse cookies in subsequent requests
4. **Estimated Effort**: 30 minutes

### Priority 2: Integrate Browser Scraper Fallback (HIGH)
1. Update `JobSourceManager.search_source()` to catch 403 errors
2. Try browser scraper when HTTP scraper fails with 403
3. Update fallback chain: API → HTTP → Browser → Error
4. **Estimated Effort**: 1 hour

### Priority 3: Improve Retry Logic for 403 (HIGH)
1. Don't treat 403 as permanent failure immediately
2. Add exponential backoff with jitter for 403 retries
3. Rotate user agent on each retry attempt
4. Try browser scraper on final retry
5. **Estimated Effort**: 1 hour

### Priority 4: Implement Human-like Delays (MEDIUM)
1. Add `_human_delay()` method to BaseJobScraper
2. Call before each request (in addition to rate limiter)
3. Integrate reading pauses (15% chance)
4. **Estimated Effort**: 1 hour

### Priority 5: Enhance Browser Scraper Stealth (MEDIUM)
1. Verify stealth mode JavaScript injection
2. Add more stealth techniques
3. Improve browser fingerprint randomization
4. **Estimated Effort**: 30 minutes

## Expected Impact

### Current State
- **Success Rate**: 0% (all 403)
- **Blocked Immediately**: Yes
- **Recovery Attempts**: None

### After Improvements
- **Target Success Rate**: 30-50% (realistic for anti-bot evasion)
- **Recovery**: Browser scraper fallback should help
- **Delays**: Human-like timing should reduce detection

## Implementation Notes

### Cookie Management
- httpx uses `response.cookies` (not `response.cookies.jar`)
- Cookies should be stored as dict: `{name: value}`
- Reuse cookies by passing to `httpx.AsyncClient(cookies=...)` or in request kwargs

### Browser Scraper Integration
- Browser scraper is async and needs proper cleanup
- Use try/finally to ensure `close()` is called
- Browser scraper is slower but more effective against anti-bot

### Retry Logic
- Exponential backoff: `delay = base * (2 ** attempt) * jitter`
- Jitter: random.uniform(0.8, 1.2)
- Max retries: 3-5 attempts before giving up

## Testing Strategy

1. **Test Each Scraper Individually**:
   - Indeed: Test with improvements
   - Glassdoor: Test with improvements
   - ZipRecruiter: Test with improvements

2. **Measure Success Rates**:
   - Before: 0% (baseline)
   - After: Target 30-50%

3. **Monitor**:
   - Response codes (200 vs 403)
   - Success rates per scraper
   - Time to success/failure

## References

- Existing Analysis: `docs/SCRAPER_TEST_ANALYSIS.md`
- Strategy Doc: `docs/ANTI_BOT_EVASION.md`
- Scraper Code: `app/services/job_scraper.py`
- Browser Scraper: `app/services/browser_scraper.py`
- Source Manager: `app/services/job_source_manager.py`

