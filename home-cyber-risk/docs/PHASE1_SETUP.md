# Phase 1 Setup Guide

## Quick Start

### 1. Test the System

Run a dry-run test to verify everything works:

```bash
cd D:\software\home-cyber-risk
python scripts/check_breaches.py --dry-run
```

**Expected output:**
- Should see "3 fetchers" initialized
- HIBP fetcher (if API key set)
- Public breach database fetcher
- Paste site fetcher

**Note:** You may see errors from paste fetcher if GitHub API rate limits are hit - this is normal and won't affect other sources.

### 2. Configure Sources

Edit your `.env` file (or set environment variables):

```bash
# Enable/disable sources (default: both enabled)
ENABLE_PUBLIC_BREACH_DB=true
ENABLE_PASTE_MONITORING=true

# Optional: GitHub token for higher rate limits (paste monitoring)
GITHUB_TOKEN=your_github_token_here

# Optional: HIBP API key for email/username checking
HIBP_API_KEY=your_hibp_api_key_here

# Cache directory for public breach data
PUBLIC_BREACH_CACHE_DIR=data/breach_cache
```

### 3. Add Public Breach Sources

Edit `services/breach_monitor/fetcher_public.py` and add URLs to the `PUBLIC_SOURCES` list:

```python
PUBLIC_SOURCES = [
    # Example: Public breach database JSON
    "https://raw.githubusercontent.com/user/repo/breaches.json",
    # Example: Public breach list CSV
    "https://example.com/breaches.csv",
]
```

**Finding Public Breach Sources:**
- Search GitHub for "breach database" or "data breach list"
- Look for JSON/CSV files with breach data
- Ensure sources are reputable and legal to use
- Consider rate limits and Terms of Service

**Note:** The public fetcher will:
- Download and cache breach data locally
- Search cached data for your identifiers
- Update cache periodically (on first check if empty)

### 4. Monitor False Positive Rate

**Target:** 5-10% false positive rate (medium tolerance)

**How to monitor:**
1. Run regular checks: `python scripts/check_breaches.py`
2. Review breach alerts carefully
3. Check if breaches are legitimate:
   - Verify breach names are real services you use
   - Check breach dates are reasonable
   - Cross-reference with HIBP if you have API key

**If false positive rate is too high:**
- Disable paste monitoring: `ENABLE_PASTE_MONITORING=false`
- Review public breach sources for quality
- Adjust risk scoring thresholds in `risk_scorer.py`

**If false positive rate is too low (missing breaches):**
- Add more public breach sources
- Enable paste monitoring if disabled
- Consider adding HIBP API key for better coverage

## Current Status

**Working:**
- Multi-source architecture (3 fetchers)
- Risk scoring system
- Cross-source aggregation
- Database schema with risk scores

**Known Issues:**
- GitHub API search may hit rate limits (60 req/hour unauthenticated)
- Public breach sources need to be configured manually
- Paste monitoring requires proper query parameter (FIXED)

## Next Actions

1. **Test the fix:** Run `python scripts/check_breaches.py --dry-run` again
2. **Add public sources:** Research and add reputable breach database URLs
3. **Configure environment:** Set up `.env` with your preferences
4. **Run real check:** Remove `--dry-run` to start storing breaches
5. **Review results:** Check database for risk scores and priorities

## Troubleshooting

**Paste fetcher errors:**
- 422 errors: Fixed - query parameter now included
- Rate limit errors: Normal, will retry with backoff
- Consider adding `GITHUB_TOKEN` for higher limits

**Public fetcher empty results:**
- No sources configured yet - add URLs to `PUBLIC_SOURCES`
- Cache may be empty - will populate on first check
- Check logs for download errors

**No breaches found:**
- This is good! Means your identifiers aren't in known breaches
- Verify sources are working by checking logs
- Consider adding HIBP API key for more comprehensive checking

