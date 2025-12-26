# Job Search Pipeline Flow Diagram

**Generated:** 2025-12-25 18:00:44

## Pipeline Overview

The job search pipeline processes requests from API endpoints through multiple stages to return matched and scored job listings.

## Flow Diagram

```mermaid
graph TD
    A["API Request<br/>POST /api/v1/jobs/search"] --> B["Request Validation<br/>jobs.py:search_jobs"]
    B --> C{"Source Filtering<br/>SUPPORTED_SOURCES"}
    C --> D["JobSourceManager<br/>Multi-Strategy Search"]

    D --> E1["API Strategy<br/>Adzuna, TheMuse, JSearch"]
    D --> E2["Browser Strategy<br/>Playwright/Selenium"]
    D --> E3["HTTP Strategy<br/>Indeed, LinkedIn, etc."]

    E1 --> F["Job Data Collection"]
    E2 --> F
    E3 --> F

    F --> G["Job Normalization<br/>Standardize format"]
    G --> H["SkillMatcher<br/>Calculate Match Scores"]

    H --> I["Database Operations<br/>Duplicate Detection"]
    I --> J{"Job Exists?"}
    J -->|Yes| K["Update Existing Job"]
    J -->|No| L["Create New Job"]

    K --> M["Commit Transaction"]
    L --> M

    M --> N["Response Formatting<br/>JobListingResponse"]
    N --> O["Return Results<br/>JobSearchResponse"]

    style A fill:#e1f5ff
    style D fill:#fff4e1
    style H fill:#e1ffe1
    style I fill:#ffe1f5
    style O fill:#e1f5ff
```

## Stage Descriptions

### 1. API Request Stage
- **Location:** `app/api/jobs.py:search_jobs`
- **Input:** `JobSearchRequest` (query, location, sources, limit, min_match_score)
- **Validation:** Source filtering, parameter validation
- **Output:** Filtered source list

### 2. JobSourceManager Stage
- **Location:** `app/services/job_source_manager.py`
- **Strategy:** Fallback chain (API → Browser → HTTP)
- **Sources:** Adzuna, TheMuse, JSearch, Indeed, LinkedIn, Glassdoor, ZipRecruiter
- **Output:** List of job dictionaries

### 3. SkillMatcher Stage
- **Location:** `app/services/skill_matcher.py`
- **Input:** Job descriptions, skill profile from database
- **Process:** 
  - Extract keywords and requirements
  - Match skills against profile
  - Calculate skill_match_score, experience_match_score, overall_match_score
- **Output:** Jobs with match scores (0.0-1.0)

### 4. Database Stage
- **Location:** `app/api/jobs.py` + `app/models/job_listing.py`
- **Process:**
  - Check for existing jobs (by source + source_id or title+company+url)
  - Create new job or update existing
  - Persist match scores, source attribution
  - Commit transaction
- **Output:** JobListing objects

### 5. Response Stage
- **Location:** `app/api/jobs.py`
- **Process:**
  - Filter by min_match_score
  - Format as JobListingResponse
  - Build JobSearchResponse with count and sources_searched
- **Output:** JSON response to client

## Data Flow

```
Request → Validation → Source Search → Normalization → Matching → Storage → Response
```

## Error Handling Points

1. **Source Failure:** Falls back to next strategy (API → Browser → HTTP)
2. **Matcher Failure:** Returns jobs without scores
3. **Database Failure:** Transaction rollback, returns partial results
4. **Validation Failure:** Returns error response immediately

## Key Components

- **JobSourceManager:** Orchestrates multi-source search with fallback
- **SkillMatcher:** Calculates relevance scores based on skill profile
- **Database Models:** JobListing, SkillProfile
- **API Schemas:** JobSearchRequest, JobSearchResponse, JobListingResponse

