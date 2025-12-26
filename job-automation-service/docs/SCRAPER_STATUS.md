# Scraper Status Documentation

**Last Updated**: December 23, 2025  
**Test Environment**: Local development

## Overview

This document tracks the status of job scrapers for different sources, including which methods work (API, Browser, HTTP) and current limitations.

## Scraper Status by Source

### Indeed

| Method | Status | Success Rate | Notes |
|--------|--------|--------------|-------|
| HTTP | ❌ Blocked | 0% | Returns 403 Forbidden immediately |
| Browser | ⚠️ Testing | Unknown | Enhanced stealth mode implemented, needs testing |
| API | ❌ Not Available | N/A | No official API available |

**Last Tested**: December 23, 2025  
**Error**: 403 Forbidden on all HTTP requests  
**Recommendation**: Use browser scraper with enhanced stealth mode

### LinkedIn

| Method | Status | Success Rate | Notes |
|--------|--------|--------------|-------|
| HTTP | ❌ Blocked | 0% | Returns 403 Forbidden immediately |
| Browser | ⚠️ Testing | Unknown | May require authentication |
| API | ⚠️ Limited | N/A | Requires partnership/authentication |

**Last Tested**: December 23, 2025  
**Error**: 403 Forbidden on all HTTP requests  
**Recommendation**: Use LinkedIn API if partnership available, otherwise browser scraper with authentication

### Glassdoor

| Method | Status | Success Rate | Notes |
|--------|--------|--------------|-------|
| HTTP | ❌ Blocked | 0% | Returns 403 Forbidden immediately |
| Browser | ⚠️ Testing | Unknown | Enhanced stealth mode implemented, needs testing |
| API | ❌ Not Available | N/A | No official API available |

**Last Tested**: December 23, 2025  
**Error**: 403 Forbidden on all HTTP requests  
**Recommendation**: Use browser scraper with enhanced stealth mode

### ZipRecruiter

| Method | Status | Success Rate | Notes |
|--------|--------|--------------|-------|
| HTTP | ❌ Blocked | 0% | Returns 403 Forbidden immediately |
| Browser | ⚠️ Testing | Unknown | Enhanced stealth mode implemented, needs testing |
| API | ❌ Not Available | N/A | No official API available |

**Last Tested**: December 23, 2025  
**Error**: 403 Forbidden on all HTTP requests  
**Recommendation**: Use browser scraper with enhanced stealth mode

## Fallback Chain

The `JobSourceManager` implements a fallback chain:

1. **API** (if available) - Most reliable, no blocking
2. **Browser Scraper** - Uses Playwright with enhanced stealth mode
3. **HTTP Scraper** - Simple HTTP requests (currently blocked)

The system automatically falls back to the next method if the previous one fails.

## Anti-Bot Evasion Techniques

### HTTP Scraper
- ✅ User-Agent rotation (12 variations)
- ✅ Accept header matching to browser type
- ✅ Accept-Language variations (7 variations)
- ✅ Sec-Fetch headers
- ✅ Referer chain support
- ✅ Cookie persistence
- ✅ Rate limiting with time-of-day delays
- ✅ Human-like delays with jitter

### Browser Scraper
- ✅ Enhanced stealth scripts:
  - Navigator property overrides (webdriver, plugins, languages)
  - WebGL fingerprint masking
  - Canvas fingerprint randomization
  - Chrome runtime object simulation
  - Battery API override
  - Connection API override
  - Device memory/hardware concurrency override
- ✅ Viewport randomization
- ✅ Human behavior simulation:
  - Realistic mouse movements
  - Natural scrolling patterns
  - Reading pauses
- ✅ Cookie management
- ✅ Referer chain support

## Testing

### Running Tests

```bash
# Test HTTP scrapers (expected to fail for blocked sources)
pytest tests/test_job_search_pipeline.py -v

# Test browser scrapers
pytest tests/test_browser_scrapers.py -v

# Test browser scraping directly
python test_browser_scraping.py
```

### Test Results

**HTTP Scraper Tests**:
- All sources return 403 Forbidden
- Tests marked with `@pytest.mark.xfail` to indicate expected failures

**Browser Scraper Tests**:
- Tests created but need execution to determine success rates
- Enhanced stealth mode implemented and ready for testing

## Troubleshooting

### Still Getting 403 Errors?

1. **Check Browser Scraping**:
   - Ensure `use_browser_scraping = True` in config
   - Verify Playwright is installed: `playwright install`
   - Check browser scraper logs

2. **Enhance Stealth Mode**:
   - Enable `stealth_mode = True` in config
   - Increase delays: `scraper_delay_min` and `scraper_delay_max`
   - Enable referer chain: `enable_referer_chain = True`

3. **Use Proxy Rotation**:
   - Configure proxy list in `app/config.py`
   - Enable `proxy_enabled = True`
   - See proxy configuration documentation

4. **Check Rate Limiting**:
   - Increase delays between requests
   - Enable human delays: `use_human_delays = True`
   - Review rate limiter logs

### Browser Scraper Not Working?

1. **Install Playwright**:
   ```bash
   playwright install
   ```

2. **Check System Requirements**:
   - Ensure Chromium can launch
   - Check system resources (memory, CPU)

3. **Review Logs**:
   - Check browser scraper error logs
   - Verify stealth scripts are injected
   - Test with simple page first (httpbin.org)

### No Jobs Returned?

1. **Verify Source is Working**:
   - Test manually in browser
   - Check if site structure changed
   - Verify selectors in scraper code

2. **Check Parsing Logic**:
   - Review HTML structure
   - Update selectors if needed
   - Test with sample HTML

## Configuration

### Key Settings

```python
# Browser Scraping
use_browser_scraping: bool = True
headless: bool = True
stealth_mode: bool = True
browser_timeout: int = 30

# Rate Limiting
scraper_delay_min: float = 2.0
scraper_delay_max: float = 8.0
use_human_delays: bool = True
enable_referer_chain: bool = True
cookie_persistence: bool = True
max_retries: int = 3

# Proxy (Future Enhancement)
proxy_enabled: bool = False
proxy_list: List[str] = []
proxy_rotation_strategy: str = "round_robin"
```

## Future Enhancements

1. **Proxy Rotation**:
   - Implement proxy rotation
   - Support residential proxies
   - Add proxy health checking

2. **CAPTCHA Solving**:
   - Integrate CAPTCHA solving service
   - Handle CAPTCHA challenges automatically

3. **Advanced Fingerprinting**:
   - More sophisticated browser profiles
   - ML-based evasion patterns
   - Dynamic fingerprint rotation

4. **Official APIs**:
   - Pursue partnerships with job sites
   - Implement official API clients
   - Prefer APIs over scraping

## Legal Considerations

⚠️ **Important**: Always:

1. Review Terms of Service for each site
2. Respect robots.txt
3. Don't overload servers
4. Use APIs when available
5. Consider legal implications
6. Implement proper rate limiting

## Related Documentation

- [Scraper Test Analysis](SCRAPER_TEST_ANALYSIS.md) - Detailed test results
- [Anti-Bot Evasion](ANTI_BOT_EVASION.md) - Evasion techniques
- [Browser Scraping](BROWSER_SCRAPING.md) - Browser scraper guide
- [Scraper Configuration](SCRAPER_CONFIG.md) - Configuration options

