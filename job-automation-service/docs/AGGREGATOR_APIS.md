# Aggregator APIs Integration Guide

## Overview

This guide explains how to use job aggregator APIs in the job automation service. Aggregator APIs provide structured access to job listings from multiple sources.

## Supported Aggregators

### 1. Adzuna API

**Status**: ✅ Implemented  
**Free Tier**: Yes  
**Coverage**: Global (US, UK, AU, etc.)

#### Setup

1. Register at https://developer.adzuna.com/
2. Get API ID and API Key
3. Configure in `.env`:

```env
ADZUNA_API_ID=your_api_id
ADZUNA_API_KEY=your_api_key
```

#### Usage

```python
from app.services.api_clients.adzuna_api import AdzunaAPIClient

client = AdzunaAPIClient()
jobs = await client.search_jobs("Python developer", "Minneapolis, MN", limit=25)
```

#### Features

- Free tier: 1000 requests/day
- Comprehensive job data
- Salary information
- Company details
- Job categories

### 2. The Muse API

**Status**: Implemented. Works without a key.
**Free tier**: 500 requests/hour without a key, 3,600/hour with one.
**Coverage**: Startup and tech roles. There is no free-text query parameter; a query that exactly matches a known category (for example `Software Engineering`) is sent as `category`. Any other query filters the fetched pages locally.

#### Setup

1. Optional: request a key from https://www.themuse.com/developers/api/v2
2. Configure in `.env` (leave as `changeme` or blank to stay unauthenticated):

```env
THEMUSE_API_KEY=changeme
```

`THE_MUSE_API_KEY` is also accepted. The key is sent only as the `api_key` query parameter and is not logged.

Location values are The Muse's own location names. An unrecognized location can return an empty page. Leave location blank to fetch a page and filter by keyword, or set a Muse location such as `Flexible / Remote`.

```python
from app.services.api_clients.the_muse_api import TheMuseAPIClient

client = TheMuseAPIClient()
jobs = await client.search_jobs("Software Engineering", "Flexible / Remote", limit=25)
```

### 2b. USAJOBS Search API

**Status**: Implemented. Disabled until both values below are set.
**Coverage**: Federal listings only (https://developer.usajobs.gov/api-reference/get-api-search).

#### Setup

```env
USAJOBS_API_KEY=changeme
USAJOBS_USER_AGENT_EMAIL=changeme
```

`USAJOBS_USER_AGENT_EMAIL` must be the email address registered with USAJOBS. It is sent as the `User-Agent` header together with `Host: data.usajobs.gov` and `Authorization-Key`. Searches send `WhoMayApply=public`. A missing value or `changeme` disables the source. The log line names the variables and does not include the key or the email.

### Adzuna retirement

Adzuna code paths are unchanged. The client is still constructed only when `ADZUNA_API_ID` and `ADZUNA_API_KEY` are set, and `adzuna` remains in the default source list. Scheduled search still does not call the Adzuna client; it calls USAJOBS and The Muse through `JobSourceManager` and keeps the existing scrapers for Indeed, LinkedIn, Glassdoor, and ZipRecruiter.

Recommendation: leave the Adzuna client in place until operators confirm the keys are revoked and draft PR #152 has landed. After that, remove `adzuna` from the default source lists and drop the browser/HTTP fallback for that name. Do not delete the client in the same change that adds USAJOBS and The Muse.

### 3. JSearch API (RapidAPI)

**Status**: ✅ Implemented  
**Free Tier**: Yes (via RapidAPI)  
**Coverage**: Multiple sources

#### Setup

1. Register at https://rapidapi.com/
2. Subscribe to JSearch API
3. Get API key
4. Configure in `.env`:

```env
JSEARCH_API_KEY=your_rapidapi_key
```

#### Usage

```python
from app.services.api_clients.jsearch_api import JSearchAPIClient

client = JSearchAPIClient()
jobs = await client.search_jobs("Python developer", "Minneapolis, MN", limit=25)
```

#### Features

- Aggregates from multiple sources
- Real-time job data
- Comprehensive job details
- Salary information

## Integration

### Via JobSourceManager

The `JobSourceManager` automatically uses aggregator APIs when configured:

```python
from app.services.job_source_manager import JobSourceManager

manager = JobSourceManager()
jobs = await manager.search_jobs(
    query="Python developer",
    location="Minneapolis, MN",
    sources=["adzuna", "the_muse", "jsearch"],
    limit=25
)
```

### Fallback Chain

For each source, the manager tries:

1. **API** (if configured) → Fast, reliable, structured data
2. **Browser Scraping** (if enabled) → Handles JavaScript-heavy sites
3. **HTTP Scraping** → Basic fallback

## Data Normalization

All API clients normalize job data to a standard format:

```python
{
    "title": str,
    "company": str,
    "location": str,
    "description": str,
    "url": str,
    "source": str,
    "source_id": str,
    "posted_date": str,
    "salary": str,
}
```

## Rate Limiting

All API clients use the `RateLimiter` to:

- Respect API rate limits
- Implement human-like delays
- Avoid overwhelming APIs

## Error Handling

API clients handle:

- HTTP errors (4xx, 5xx)
- Network timeouts
- Invalid responses
- Missing credentials

## Best Practices

1. **API Keys**: Store in `.env`, never commit
2. **Rate Limits**: Monitor usage
3. **Error Handling**: Implement retries
4. **Data Validation**: Verify job data quality
5. **Cost Monitoring**: Track API usage

## Comparison

| Feature | Adzuna | The Muse | JSearch |
|---------|--------|----------|---------|
| Free Tier | ✅ | Limited | ✅ |
| Coverage | Global | US-focused | Multiple |
| Salary Data | ✅ | ❌ | ✅ |
| Company Info | ✅ | ✅ | ✅ |
| Rate Limits | 1000/day | Varies | Varies |

## Future Aggregators

Potential additions:

- **SerpAPI**: Google Jobs search
- **Jobs API**: Another aggregator
- **Careerjet**: Job search API
- **Jooble**: Job aggregator API

## Troubleshooting

### No Jobs Returned

1. Check API credentials
2. Verify API key is active
3. Check rate limits
4. Review API documentation

### Authentication Errors

1. Verify API key format
2. Check key expiration
3. Review API status page

### Rate Limit Errors

1. Reduce request frequency
2. Implement exponential backoff
3. Consider upgrading tier

