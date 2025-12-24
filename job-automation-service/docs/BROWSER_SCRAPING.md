# Browser Scraping Guide

## Overview

This guide explains how browser-based scraping works in the job automation service. Browser scraping uses Playwright to execute JavaScript and mimic real browser behavior, helping bypass anti-bot measures.

## Architecture

### BrowserJobScraper

The `BrowserJobScraper` class extends `BaseJobScraper` and uses Playwright to:

- Execute JavaScript (required by many modern sites)
- Maintain cookies and sessions
- Simulate human behavior (mouse movements, scrolling)
- Use realistic browser fingerprints
- Handle dynamic content loading

### Key Features

1. **Stealth Mode**: Removes automation indicators
2. **Cookie Management**: Persists cookies across requests
3. **Referer Chains**: Maintains navigation history
4. **Human Simulation**: Random delays, mouse movements, scrolling

## Configuration

In `app/config.py`:

```python
# Browser Scraping Configuration
use_browser_scraping: bool = True
browser_type: str = "playwright"  # or "selenium"
headless: bool = True
browser_timeout: int = 30
stealth_mode: bool = True
```

## Usage

### Direct Usage

```python
from app.services.browser_scraper import BrowserJobScraper

scraper = BrowserJobScraper("indeed")
html = await scraper._fetch_page("https://www.indeed.com/jobs?q=python")
await scraper.close()
```

### Via JobSourceManager

The `JobSourceManager` automatically uses browser scraping as a fallback:

1. Try API first (if available)
2. Fallback to browser scraping
3. Fallback to HTTP scraping

## Anti-Bot Evasion

### Stealth Scripts

The browser scraper injects scripts to:

- Hide `navigator.webdriver` property
- Add realistic plugins
- Set proper language preferences
- Add Chrome runtime object

### Human Behavior Simulation

- Random mouse movements
- Variable scrolling
- Reading pauses (2-5 seconds)
- Time-based delays

## Performance Considerations

### Resource Usage

- **Memory**: ~100-200MB per browser instance
- **CPU**: Moderate (JavaScript execution)
- **Network**: Slower than HTTP (full page load)

### Optimization Tips

1. Reuse browser instances when possible
2. Close browsers promptly after use
3. Use headless mode (default)
4. Limit concurrent browser instances

## Troubleshooting

### Common Issues

1. **Browser not starting**
   - Ensure Playwright is installed: `playwright install`
   - Check system requirements

2. **Timeouts**
   - Increase `browser_timeout` in config
   - Check network connectivity

3. **Still getting blocked**
   - Enable `stealth_mode`
   - Increase delays
   - Use proxies (future enhancement)

## Best Practices

1. **Respect Rate Limits**: Use rate limiter
2. **Handle Errors**: Implement retry logic
3. **Clean Up**: Always close browsers
4. **Monitor**: Log browser activity
5. **Test**: Verify with real sites

## Future Enhancements

- Proxy rotation
- Browser fingerprint rotation
- CAPTCHA solving integration
- Session persistence across restarts

