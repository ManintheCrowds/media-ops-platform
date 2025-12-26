# Configuration Guide

## Environment Variables

### Core Configuration

- `HIBP_API_KEY`: Optional HIBP API key for email/username/domain checking (paid feature)
- `DATABASE_URL`: Database connection string (default: `sqlite:///data/breaches.db`)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, default: INFO)
- `LOKI_URL`: Optional Loki URL for log aggregation

### Multi-Source Configuration

- `ENABLE_PUBLIC_BREACH_DB`: Enable public breach database API fetcher (default: `true`)
- `ENABLE_PWDB_PUBLIC`: Enable Pwdb-Public fetcher via GitHub API (default: `true`)
- `ENABLE_PASTE_MONITORING`: Enable paste site monitoring (default: `true`)
- `GITHUB_TOKEN`: Optional GitHub token for higher API rate limits (recommended for Pwdb-Public and paste monitoring)

### Alert Configuration

See existing alert configuration in main README for email, Telegram, and webhook settings.

## Identifiers Configuration

Edit `config/identifiers.yml` to specify what to monitor:

```yaml
emails:
  - "your-email@example.com"

usernames:
  - "your-username"

domains:
  - "example.com"

# Optional source preferences
source_preferences:
  emails: [hibp, public_db, pwdb, paste]
  usernames: [public_db, pwdb, paste]
  domains: [hibp]
```

### Source Preferences

You can specify which sources to use for each identifier type:

- `hibp`: Have I Been Pwned API (requires API key for email/username)
- `public_db`: Public breach database APIs (free, configurable endpoints)
- `pwdb`: Pwdb-Public database via GitHub API (free, requires GitHub token for higher limits)
- `paste`: Paste site monitoring (free)

If not specified, all enabled sources will be used.

## Data Sources

### HIBP (Have I Been Pwned)
- **Cost**: Free for password checking, $3.50/month for email/username/domain
- **Rate Limit**: 200ms between requests
- **Coverage**: Comprehensive, verified breaches

### Public Breach Databases
- **Cost**: Free
- **Rate Limit**: Varies by source
- **Coverage**: Public breach lists, GitHub repos

### Paste Sites
- **Cost**: Free
- **Rate Limit**: 60 requests/hour (GitHub API, unauthenticated)
- **Coverage**: GitHub Gists, Pastebin (if implemented)

## Risk Scoring

Breaches are automatically scored and prioritized:

- **Critical** (80+): Passwords exposed, very recent, verified
- **High** (60-79): Sensitive data exposed, recent
- **Medium** (40-59): Moderate risk
- **Low** (<40): Lower risk, older breaches

Risk score factors:
- Data classes exposed (passwords = highest)
- Breach recency (recent = higher)
- Verification status (verified = higher)
- Pwn count (widespread = higher)

## Multi-Source Aggregation

When multiple sources find the same breach:
- Breaches are deduplicated by identifier and breach name
- Data classes are merged (union)
- Most recent breach date is used
- Highest pwn count is used
- Confidence score increases with more sources

Confidence scores:
- 1 source: 0.6 (moderate)
- 2 sources: 0.8 (high)
- 3+ sources: 1.0 (very high)

