# Scraper Configuration Guide

This document explains all configuration options for job scrapers.

## Browser Scraping Configuration

### `use_browser_scraping`
- **Type**: `bool`
- **Default**: `True`
- **Description**: Enable browser-based scraping using Playwright
- **When to Use**: When HTTP scrapers are blocked (403 errors)

### `browser_type`
- **Type**: `str`
- **Default**: `"playwright"`
- **Options**: `"playwright"`, `"selenium"`
- **Description**: Browser automation library to use
- **Note**: Currently only Playwright is implemented

### `headless`
- **Type**: `bool`
- **Default**: `True`
- **Description**: Run browser in headless mode (no GUI)
- **When to Use**: Production environments, faster execution
- **When Not to Use**: Debugging (set to `False` to see browser)

### `browser_timeout`
- **Type**: `int`
- **Default**: `30`
- **Description**: Maximum wait time for page load (seconds)
- **When to Increase**: Slow network, JavaScript-heavy pages

### `stealth_mode`
- **Type**: `bool`
- **Default**: `True`
- **Description**: Enable enhanced stealth mode (anti-detection)
- **Features**:
  - Navigator property overrides
  - WebGL fingerprint masking
  - Canvas fingerprint randomization
  - Human behavior simulation

## Rate Limiting Configuration

### `scraper_delay_min`
- **Type**: `float`
- **Default**: `2.0`
- **Description**: Minimum delay between requests (seconds)
- **When to Increase**: Getting rate limited, want to be more respectful

### `scraper_delay_max`
- **Type**: `float`
- **Default**: `8.0`
- **Description**: Maximum delay between requests (seconds)
- **When to Increase**: Getting rate limited, want to be more respectful

### `use_human_delays`
- **Type**: `bool`
- **Default**: `True`
- **Description**: Use time-of-day based delays (simulate human behavior)
- **Multipliers**:
  - Business hours (9 AM - 5 PM): 0.8x (faster)
  - Evening (5 PM - 10 PM): 1.0x (normal)
  - Night (10 PM - 6 AM): 1.3x (slower)
  - Early morning (6 AM - 9 AM): 1.1x (slightly slower)

### `max_retries`
- **Type**: `int`
- **Default**: `3`
- **Description**: Maximum retry attempts on failure
- **When to Increase**: Unstable network, temporary errors

## Header Configuration

### `enable_referer_chain`
- **Type**: `bool`
- **Default**: `True`
- **Description**: Maintain referer chain (simulate navigation)
- **When to Use**: Most cases (improves anti-bot evasion)
- **When Not to Use**: First request to a site

### `cookie_persistence`
- **Type**: `bool`
- **Default**: `True`
- **Description**: Save and reuse cookies across requests
- **When to Use**: Most cases (maintains session)
- **When Not to Use**: Testing, want fresh session

## Proxy Configuration (Future Enhancement)

### `proxy_enabled`
- **Type**: `bool`
- **Default**: `False`
- **Description**: Enable proxy rotation
- **Status**: Not yet implemented
- **Future Use**: Distribute requests across IPs

### `proxy_list`
- **Type**: `List[str]`
- **Default**: `[]`
- **Description**: List of proxy URLs (e.g., `["http://proxy1:8080", "http://proxy2:8080"]`)
- **Status**: Not yet implemented
- **Format**: `http://username:password@host:port` or `http://host:port`

### `proxy_rotation_strategy`
- **Type**: `str`
- **Default**: `"round_robin"`
- **Options**: `"round_robin"`, `"random"`, `"least_used"`
- **Description**: Strategy for selecting proxy
- **Status**: Not yet implemented

## API Configuration

### `indeed_api_key`
- **Type**: `Optional[str]`
- **Default**: `None`
- **Description**: API key for Indeed (if available)
- **Status**: Not available

### `linkedin_api_key`
- **Type**: `Optional[str]`
- **Default**: `None`
- **Description**: API key for LinkedIn (requires partnership)
- **Status**: Requires partnership

### `glassdoor_api_key`
- **Type**: `Optional[str]`
- **Default**: `None`
- **Description**: API key for Glassdoor (if available)
- **Status**: Not available

### `ziprecruiter_api_key`
- **Type**: `Optional[str]`
- **Default**: `None`
- **Description**: API key for ZipRecruiter (if available)
- **Status**: Not available

### `adzuna_api_key` / `adzuna_api_id`
- **Type**: `Optional[str]`
- **Default**: `None`
- **Description**: API credentials for Adzuna
- **Status**: Available (working)

### `jsearch_api_key`
- **Type**: `Optional[str]`
- **Default**: `None`
- **Description**: API key for JSearch (RapidAPI)
- **Status**: Available (working)

## Configuration Examples

### Production (Respectful Scraping)
```python
use_browser_scraping = True
stealth_mode = True
scraper_delay_min = 5.0
scraper_delay_max = 15.0
use_human_delays = True
enable_referer_chain = True
cookie_persistence = True
max_retries = 3
```

### Development (Faster Testing)
```python
use_browser_scraping = True
headless = False  # See browser for debugging
stealth_mode = True
scraper_delay_min = 1.0
scraper_delay_max = 3.0
use_human_delays = False  # Faster for testing
max_retries = 1
```

### Aggressive (Higher Risk of Blocking)
```python
use_browser_scraping = True
stealth_mode = True
scraper_delay_min = 2.0
scraper_delay_max = 5.0
use_human_delays = True
enable_referer_chain = True
cookie_persistence = True
max_retries = 5
```

## Environment Variables

All settings can be overridden via environment variables:

```bash
# Browser Scraping
USE_BROWSER_SCRAPING=true
HEADLESS=true
STEALTH_MODE=true
BROWSER_TIMEOUT=30

# Rate Limiting
SCRAPER_DELAY_MIN=2.0
SCRAPER_DELAY_MAX=8.0
USE_HUMAN_DELAYS=true
MAX_RETRIES=3

# Headers
ENABLE_REFERER_CHAIN=true
COOKIE_PERSISTENCE=true

# API Keys
ADZUNA_API_KEY=your_key
ADZUNA_API_ID=your_id
JSEARCH_API_KEY=your_key
```

## Best Practices

1. **Start Conservative**: Use longer delays initially
2. **Monitor Success Rates**: Track which sources work
3. **Adjust Based on Results**: Increase delays if getting blocked
4. **Use Browser Scraping**: When HTTP scrapers fail
5. **Enable Stealth Mode**: Always for production
6. **Respect Rate Limits**: Don't overwhelm servers
7. **Use APIs When Available**: More reliable than scraping

## Troubleshooting

### Getting Blocked?
- Increase delays (`scraper_delay_min`, `scraper_delay_max`)
- Enable stealth mode (`stealth_mode = True`)
- Use browser scraping (`use_browser_scraping = True`)
- Enable referer chain (`enable_referer_chain = True`)

### Slow Performance?
- Reduce delays (but risk blocking)
- Disable human delays (`use_human_delays = False`)
- Use headless mode (`headless = True`)
- Reduce retries (`max_retries = 1`)

### Browser Not Starting?
- Install Playwright: `playwright install`
- Check system requirements
- Try non-headless mode for debugging
- Check browser timeout settings

## Related Documentation

- [Scraper Status](SCRAPER_STATUS.md) - Current status of scrapers
- [Anti-Bot Evasion](ANTI_BOT_EVASION.md) - Evasion techniques
- [Browser Scraping](BROWSER_SCRAPING.md) - Browser scraper guide

