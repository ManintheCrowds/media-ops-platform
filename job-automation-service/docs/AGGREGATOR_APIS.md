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

**Status**: ✅ Implemented  
**Free Tier**: Limited  
**Coverage**: Startup-focused jobs

#### Setup

1. Register at https://www.themuse.com/developers/api/v2
2. Get API key
3. Configure in `.env`:

```env
THE_MUSE_API_KEY=your_api_key
```

#### Usage

```python
from app.services.api_clients.the_muse_api import TheMuseAPIClient

client = TheMuseAPIClient()
jobs = await client.search_jobs("Python developer", "Minneapolis, MN", limit=25)
```

#### Features

- Startup and tech company focus
- Company culture information
- Job categories
- Location filtering

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

