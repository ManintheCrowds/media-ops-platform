# Job Automation Service API Documentation

**Version:** 1.0  
**Base URL:** `http://localhost:8004/api/v1`

## Overview

The Job Automation Service provides APIs for job searching, matching, application tracking, and scheduling.

## Authentication

Currently, no authentication is required for development. For production, implement authentication (OAuth2, API keys, etc.).

## Endpoints

### Jobs

#### Search Jobs

```http
POST /api/v1/jobs/search
```

Search for jobs across multiple sources.

**Request Body:**
```json
{
  "query": "Python developer",
  "location": "Minneapolis, MN",
  "limit": 25,
  "min_match_score": 0.5,
  "sources": ["indeed", "linkedin"]
}
```

**Response:**
```json
{
  "jobs": [
    {
      "id": 1,
      "title": "Python Developer",
      "company": "Tech Corp",
      "location": "Minneapolis, MN",
      "source": "indeed",
      "url": "https://...",
      "overall_match_score": 0.85,
      "skill_match_score": 0.9,
      "experience_match_score": 0.8
    }
  ],
  "total": 1,
  "sources_searched": ["indeed", "linkedin"]
}
```

#### List Jobs

```http
GET /api/v1/jobs?min_score=0.7&source=indeed&limit=50&offset=0
```

List saved job listings with filtering.

**Query Parameters:**
- `min_score` (float, optional): Minimum match score (0.0-1.0)
- `source` (string, optional): Filter by source
- `active_only` (boolean, default: true): Only active jobs
- `limit` (int, default: 50): Results per page (1-100)
- `offset` (int, default: 0): Pagination offset

**Response:**
```json
[
  {
    "id": 1,
    "title": "Python Developer",
    "company": "Tech Corp",
    "location": "Minneapolis, MN",
    "overall_match_score": 0.85
  }
]
```

#### Get Job by ID

```http
GET /api/v1/jobs/{job_id}
```

Get a specific job listing.

**Response:**
```json
{
  "id": 1,
  "title": "Python Developer",
  "company": "Tech Corp",
  "location": "Minneapolis, MN",
  "description": "...",
  "requirements": "...",
  "overall_match_score": 0.85
}
```

#### Get Recommended Jobs

```http
GET /api/v1/jobs/recommended?min_score=0.7&limit=20
```

Get recommended jobs based on match score.

**Query Parameters:**
- `min_score` (float, default: 0.7): Minimum match score
- `limit` (int, default: 20): Maximum results (1-50)

**Response:**
```json
[
  {
    "id": 1,
    "title": "Python Developer",
    "company": "Tech Corp",
    "overall_match_score": 0.85
  }
]
```

### Applications

#### Create Application

```http
POST /api/v1/applications
```

Create a new job application.

**Request Body:**
```json
{
  "job_listing_id": 1,
  "status": "applied",
  "notes": "Applied via company website",
  "generate_cover_letter": true
}
```

**Response:**
```json
{
  "id": 1,
  "job_listing_id": 1,
  "status": "applied",
  "applied_at": "2025-12-23T10:00:00Z",
  "cover_letter": "Dear Hiring Manager..."
}
```

#### List Applications

```http
GET /api/v1/applications?status=applied&limit=50
```

List all applications.

**Query Parameters:**
- `status` (string, optional): Filter by status
- `limit` (int, default: 50): Results per page
- `offset` (int, default: 0): Pagination offset

#### Get Application by ID

```http
GET /api/v1/applications/{application_id}
```

Get a specific application.

#### Schedule Follow-up

```http
POST /api/v1/applications/{application_id}/followup
```

Schedule a follow-up for an application.

**Request Body:**
```json
{
  "days": 7,
  "notes": "Follow up on application status"
}
```

**Response:**
```json
{
  "id": 1,
  "next_followup": "2025-12-30T10:00:00Z",
  "followup_count": 1
}
```

### Matching

#### Score Job

```http
POST /api/v1/matching/score
```

Score a job description against skill profile.

**Request Body:**
```json
{
  "job_description": "Python developer with FastAPI experience"
}
```

**Response:**
```json
{
  "skill_match_score": 0.85,
  "experience_match_score": 0.80,
  "overall_match_score": 0.83,
  "matched_skills": [
    {
      "skill": "Python",
      "proficiency": 5,
      "category": "technical"
    }
  ]
}
```

#### Batch Score Jobs

```http
POST /api/v1/matching/batch-score
```

Score multiple job descriptions.

**Request Body:**
```json
{
  "job_descriptions": [
    "Python developer",
    "Java developer"
  ]
}
```

**Response:**
```json
{
  "scores": [
    {
      "skill_match_score": 0.85,
      "experience_match_score": 0.80,
      "overall_match_score": 0.83,
      "matched_skills": [...]
    }
  ]
}
```

#### Get Matching Stats

```http
GET /api/v1/matching/stats
```

Get matching statistics.

**Response:**
```json
{
  "total_jobs": 100,
  "average_match_score": 0.65,
  "high_match_jobs": 25,
  "medium_match_jobs": 40,
  "low_match_jobs": 35,
  "top_matched_skills": [],
  "skill_profile_summary": {
    "total_skills": 28,
    "categories": {
      "technical": 20,
      "soft": 8
    }
  }
}
```

### Scheduler

#### Start Scheduler

```http
POST /api/v1/scheduler/start
```

Start the job search scheduler.

**Request Body (optional):**
```json
{
  "queries": ["Python developer"],
  "location": "Minneapolis, MN",
  "sources": ["indeed", "linkedin"],
  "min_match_score": 0.7,
  "limit_per_query": 10
}
```

**Response:**
```json
{
  "message": "Scheduler started",
  "status": "running",
  "location": "Minneapolis, MN"
}
```

#### Stop Scheduler

```http
POST /api/v1/scheduler/stop
```

Stop the job search scheduler.

**Response:**
```json
{
  "message": "Scheduler stopped",
  "status": "stopped"
}
```

#### Trigger Search

```http
POST /api/v1/scheduler/search
```

Trigger a one-time job search.

**Request Body:**
```json
{
  "queries": ["Python developer"],
  "location": "Minneapolis, MN",
  "sources": ["indeed"],
  "min_match_score": 0.7,
  "limit_per_query": 10
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

Rate limiting is implemented for scrapers:
- Default delay: 2 seconds between requests
- Configurable via `scraper_rate_limit_delay` setting

## Examples

### Python

```python
import httpx

async with httpx.AsyncClient() as client:
    # Search jobs
    response = await client.post(
        "http://localhost:8004/api/v1/jobs/search",
        json={
            "query": "Python developer",
            "location": "Minneapolis, MN",
            "limit": 10
        }
    )
    jobs = response.json()
    
    # Score a job
    score_response = await client.post(
        "http://localhost:8004/api/v1/matching/score",
        json={"job_description": "Python developer with FastAPI"}
    )
    score = score_response.json()
```

### cURL

```bash
# Search jobs
curl -X POST http://localhost:8004/api/v1/jobs/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python developer",
    "location": "Minneapolis, MN",
    "limit": 10
  }'

# Score job
curl -X POST http://localhost:8004/api/v1/matching/score \
  -H "Content-Type: application/json" \
  -d '{"job_description": "Python developer with FastAPI"}'
```

## OpenAPI/Swagger

Interactive API documentation available at:
- Swagger UI: `http://localhost:8004/docs`
- ReDoc: `http://localhost:8004/redoc`
- OpenAPI JSON: `http://localhost:8004/openapi.json`

