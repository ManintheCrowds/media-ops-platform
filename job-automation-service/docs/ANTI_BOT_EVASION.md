# Anti-Bot Evasion Techniques

## Overview

This document describes the anti-bot evasion techniques implemented in the job automation service to reduce the likelihood of being blocked by job sites.

## Strategy Overview

We use a multi-layered approach:

1. **Enhanced HTTP Headers** - Realistic browser headers
2. **Human-like Delays** - Variable, time-based delays
3. **Cookie Management** - Session persistence
4. **Referer Chains** - Maintain navigation history
5. **Browser Automation** - Execute JavaScript (Playwright)
6. **User Agent Rotation** - Vary browser fingerprints

## HTTP Header Enhancements

### Standard Headers

```python
{
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}
```

### Sec-Fetch Headers

Modern browsers send Sec-Fetch headers:

```python
{
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",  # or "same-origin" / "cross-site"
    "Sec-Fetch-User": "?1",
}
```

### Referer Headers

Maintain referer chain to simulate navigation:

```python
if previous_url:
    headers["Referer"] = previous_url
```

## Human-like Delays

### Time-Based Multipliers

Delays vary by time of day:

- **Business Hours (9 AM - 5 PM)**: 0.8x (faster)
- **Evening (5 PM - 10 PM)**: 1.0x (normal)
- **Night (10 PM - 6 AM)**: 1.3x (slower)
- **Early Morning (6 AM - 9 AM)**: 1.1x (slightly slower)

### Random Variations

- Base delay: 2-8 seconds (configurable)
- Jitter: ±10% random variation
- Reading pauses: 15% chance of 2-5 second extra pause

### Exponential Backoff

On errors, delays increase exponentially:

```python
delay = base_delay * (2 ** attempt) * jitter
```

## Cookie Management

### Session Persistence

- Save cookies from responses
- Reuse cookies in subsequent requests
- Maintain session state

### Cookie Rotation

- Rotate cookies periodically
- Handle cookie expiration
- Support multiple sessions

## Browser Automation

### Stealth Mode

Remove automation indicators:

```javascript
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});
```

### Human Behavior Simulation

- Random mouse movements
- Variable scrolling
- Reading pauses
- Natural interaction patterns

## User Agent Rotation

### Rotation Strategy

- Random selection from pool
- Match User-Agent to other headers
- Update per request

### User Agent Pool

Multiple realistic user agents:

- Chrome (Windows, Mac, Linux)
- Firefox (Windows, Mac)
- Safari (Mac)

## Configuration

### Settings

```python
# Rate Limiting
scraper_delay_min: float = 2.0
scraper_delay_max: float = 8.0
use_human_delays: bool = True

# Headers
enable_referer_chain: bool = True

# Cookies
cookie_persistence: bool = True

# Browser
use_browser_scraping: bool = True
stealth_mode: bool = True
```

## Best Practices

### 1. Gradual Scaling

- Start with low frequency
- Gradually increase
- Monitor success rates

### 2. Error Handling

- Implement retries with backoff
- Log all errors
- Track success rates

### 3. Monitoring

- Track request success rates
- Monitor response times
- Alert on high error rates

### 4. Respect Limits

- Follow robots.txt
- Respect rate limits
- Don't overwhelm servers

## Limitations

### What We Can't Bypass

1. **IP-based blocking** - Requires proxies
2. **CAPTCHA** - Requires solving service
3. **Advanced fingerprinting** - Requires more sophisticated techniques
4. **Behavioral analysis** - Requires ML-based evasion

### When to Use APIs

If available, prefer official APIs:

- More reliable
- Better data quality
- No blocking concerns
- Legal compliance

## Future Enhancements

1. **Proxy Rotation** - Distribute requests across IPs
2. **CAPTCHA Solving** - Integrate solving services
3. **Advanced Fingerprinting** - More sophisticated browser profiles
4. **ML-based Evasion** - Learn from successful patterns

## Legal Considerations

⚠️ **Important**: Always:

1. Review Terms of Service
2. Respect robots.txt
3. Don't overload servers
4. Use APIs when available
5. Consider legal implications

## Testing

### Test Scenarios

1. **Single Request**: Verify headers and delays
2. **Multiple Requests**: Test rate limiting
3. **Error Handling**: Test retry logic
4. **Cookie Persistence**: Verify session maintenance

### Monitoring

Track:

- Success rates
- Response times
- Error types
- Block rates

## Troubleshooting

### Still Getting Blocked?

1. **Increase Delays**: Make requests slower
2. **Use Browser**: Enable browser scraping
3. **Check Headers**: Verify all headers present
4. **Review Logs**: Check for patterns
5. **Try APIs**: Use official APIs if available

### High Error Rates?

1. **Check Network**: Verify connectivity
2. **Review Rate Limits**: Reduce frequency
3. **Update Headers**: Ensure realistic headers
4. **Enable Stealth**: Use browser with stealth mode

