# Breach Detection Guide

## Overview

The security service provides comprehensive breach detection and password validation capabilities using **free** services:

- **HIBP Pwned Passwords API** (free, no API key required) - Password checking
- **Public breach sources** (free) - Email and domain breach checking

This integration helps protect user accounts by:

- Checking passwords against the Pwned Passwords database during registration
- Monitoring user emails for data breaches using public sources
- Tracking domain-level breaches for organizational security
- Providing proactive breach notifications

## Features

### 1. Password Breach Checking

Passwords are automatically checked against HIBP's Pwned Passwords database (over 11 billion compromised passwords) during user registration. Breached passwords are rejected with a user-friendly error message.

**Implementation:**
- Uses k-anonymity model (only first 5 characters of SHA-1 hash sent to API)
- No plain-text passwords are transmitted
- Fail-open design (doesn't block registration if service unavailable)

### 2. Email Breach Detection

User email addresses are checked against public breach databases:
- During registration (warns but doesn't block)
- Periodic scanning of all active users
- Automatic breach record storage and tracking
- Uses local breach database (downloaded from public sources)

### 3. Domain Breach Monitoring

Organizational domains can be monitored for breaches:
- Configure domains via `SECURITY_BREACH_MONITORED_DOMAINS`
- Periodic checks for new domain breaches
- Alert generation when breaches detected
- Uses local breach database aggregated from public sources

### 4. Breach History Tracking

All breach data is stored in the database:
- `UserBreach` - Tracks breaches per user email
- `DomainBreach` - Tracks breaches per monitored domain
- `BreachHistory` - Historical breach information

## Configuration

### Environment Variables

```bash
# Feature flags (all free, no API key required)
SECURITY_HIBP_ENABLE_PASSWORD_CHECK=true  # Uses free HIBP Pwned Passwords API
SECURITY_HIBP_ENABLE_EMAIL_CHECK=true  # Uses free public breach sources

# Cache settings
SECURITY_HIBP_CACHE_TTL=3600  # 1 hour default

# Rate limiting (for password API)
SECURITY_HIBP_RATE_LIMIT_DELAY=0.2  # 200ms between requests

# Domain monitoring
SECURITY_BREACH_MONITORED_DOMAINS=example.com,company.com
SECURITY_HIBP_DOMAIN_CHECK_INTERVAL=86400  # 24 hours

# Public breach sources (optional - URLs/repos for breach data)
SECURITY_PUBLIC_BREACH_SOURCES=https://raw.githubusercontent.com/user/repo/breaches.json

# Breach database update configuration
SECURITY_BREACH_DATA_UPDATE_INTERVAL=86400  # 24 hours
SECURITY_BREACH_DATA_CACHE_DIR=/var/cache/breach-data
```

### Public Breach Sources

The system uses free public breach sources for email/domain checking. You can configure additional sources:

1. **GitHub Repositories**: Add URLs to breach data files (JSON, CSV, TXT)
2. **Public APIs**: Add URLs to breach data endpoints
3. **Local Files**: The system will cache downloaded data locally

**Note:** Password checking uses the free HIBP Pwned Passwords API (no configuration needed).

## API Endpoints

### Get User Breaches

```http
GET /api/security/breaches/user/{user_id}
```

Returns all breaches for a specific user.

### Check Email

```http
GET /api/security/breaches/email/{email}?force_refresh=false
```

Check a specific email address for breaches.

### Get Domain Breaches

```http
GET /api/security/breaches/domain/{domain}
```

Get breach status for a monitored domain.

### Check Password (Admin)

```http
POST /api/security/breaches/check-password
Content-Type: application/json

{
  "password": "password-to-check"
}
```

Check if a password has been pwned (admin only).

### Breach Statistics

```http
GET /api/security/breaches/stats
```

Get overall breach statistics.

## Integration Points

### User Registration

The authentication service (`app/auth/oauth2.py`) automatically:
1. Checks password against Pwned Passwords database
2. Rejects breached passwords with error message
3. Checks email against breach database
4. Warns (but doesn't block) if email is breached
5. Stores breach information in database

### Periodic Monitoring

The breach monitor service can be scheduled to:
- Scan all active user emails daily
- Check monitored domains for new breaches
- Generate alerts for new breaches

**Example scheduled task:**
```python
from security_service.monitoring.breach_monitor import BreachMonitor
from app.models import User

# In your scheduler
monitor = BreachMonitor(db)
results = await monitor.scan_all_users(User)
```

## Security Considerations

### Privacy

- Passwords are hashed (SHA-1) before API calls
- Only hash prefixes sent to Pwned Passwords API (k-anonymity)
- Email addresses checked against local breach database (no external API calls)
- Breach data stored securely in database
- No plain-text passwords stored or transmitted

### Rate Limiting

- HIBP Pwned Passwords API requires 200ms delay between requests
- Automatic exponential backoff on 429 responses
- Aggressive caching to minimize API calls
- Email/domain checking uses local database (no rate limits)

### Fail-Safe Design

- Password checking fails open (doesn't block if service unavailable)
- Email checking warns but doesn't block registration
- All errors are logged but don't break user flows

## Alerting

Breach detection triggers alerts through configured channels:

- **Email Breach**: High severity alert when user email found in breach
- **Domain Breach**: Critical severity alert for domain breaches
- **Password Breach Attempt**: Medium severity for blocked registrations
- **Multiple Breaches**: Critical alert when user has 5+ breaches

## Compliance Reporting

Breach statistics are included in security audit reports:

- Total user breaches detected
- Unique emails breached
- Domain breaches
- Password breach attempts blocked

## Troubleshooting

### Breach Database Issues

**Error:** "No breach data available"
- Ensure public breach sources are configured (optional)
- The system will download breach data automatically on first use
- Check `SECURITY_BREACH_DATA_CACHE_DIR` is writable
- Run breach database update manually if needed

### Rate Limiting

**Error:** "Rate limit exceeded"
- Increase `HIBP_RATE_LIMIT_DELAY` (default 200ms)
- Reduce batch sizes in monitoring tasks
- Check cache TTL settings

### Service Unavailable

**Error:** "HIBP request failed"
- Check network connectivity
- Verify HIBP API status
- Review error logs for details
- Service fails open (doesn't block operations)

## Best Practices

1. **Regular Monitoring**: Schedule daily breach scans for all users
2. **Domain Monitoring**: Configure all organizational domains
3. **User Notification**: Notify users when breaches detected
4. **Password Policy**: Enforce strong passwords in addition to breach checking
5. **Cache Management**: Adjust cache TTL based on update frequency needs
6. **Breach Database Updates**: Configure automatic updates from public sources
7. **Public Sources**: Add multiple breach sources for better coverage

## Attribution

This integration uses data from [Have I Been Pwned](https://haveibeenpwned.com/) by Troy Hunt. Per the Creative Commons Attribution License, proper attribution is required when displaying breach data to users.

## Public Breach Sources

### Overview

Email and domain breach checking uses free public breach sources. The system downloads breach data from configured sources and stores it in a local database for fast lookups.

### Configuring Sources

Add public breach source URLs to your `.env` file:

```bash
SECURITY_PUBLIC_BREACH_SOURCES=https://raw.githubusercontent.com/user/repo/breaches.json,https://example.com/breach-list.csv
```

### Supported Formats

1. **JSON Format:**
   ```json
   {
     "breaches": [
       {
         "email": "user@example.com",
         "breach_name": "ExampleBreach",
         "breach_date": "2024-01-01",
         "data_classes": ["Email addresses", "Passwords"]
       }
     ]
   }
   ```

2. **CSV Format:**
   ```csv
   email,breach_name,breach_date
   user@example.com,ExampleBreach,2024-01-01
   ```

3. **Text Format:**
   ```
   user1@example.com
   user2@example.com
   user3@example.com
   ```

### Updating the Database

Trigger database updates on-demand via API:

```bash
POST /api/security/breaches/update-database?force=false
```

Or use the population script:

```bash
python scripts/populate_breach_database.py
```

### Finding Public Breach Sources

When researching public breach sources, look for:
- GitHub repositories with breach data (JSON/CSV files)
- Security researcher publications
- Public breach databases
- Open-source security projects

**Important:** Only use reputable, legal sources. Ensure you have permission to use the data and comply with all applicable laws and regulations.

### Source Requirements

- Must be publicly accessible (no authentication required)
- Must be in JSON, CSV, or text format
- Should include email addresses and breach metadata
- Should be regularly updated

## References

- [HIBP Pwned Passwords API](https://haveibeenpwned.com/API/v3#PwnedPasswords) (Free)
- [Security Framework Documentation](./SECURITY_FRAMEWORK.md)
- [Breach Intake Guide](./BREACH_INTAKE_GUIDE.md)

