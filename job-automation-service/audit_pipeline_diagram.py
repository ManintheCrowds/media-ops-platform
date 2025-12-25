"""Pipeline Flow Diagram Generator - Generate visual representation of the pipeline."""

from pathlib import Path
from datetime import datetime

# Base directory
BASE_DIR = Path(__file__).parent


def generate_pipeline_diagram() -> str:
    """Generate Mermaid diagram showing the pipeline flow."""
    
    timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Build mermaid diagram as separate string to avoid format issues with curly braces
    mermaid_lines = [
        "graph TD",
        '    A["API Request<br/>POST /api/v1/jobs/search"] --> B["Request Validation<br/>jobs.py:search_jobs"]',
        '    B --> C{"Source Filtering<br/>SUPPORTED_SOURCES"}',
        '    C --> D["JobSourceManager<br/>Multi-Strategy Search"]',
        "",
        '    D --> E1["API Strategy<br/>Adzuna, TheMuse, JSearch"]',
        '    D --> E2["Browser Strategy<br/>Playwright/Selenium"]',
        '    D --> E3["HTTP Strategy<br/>Indeed, LinkedIn, etc."]',
        "",
        '    E1 --> F["Job Data Collection"]',
        "    E2 --> F",
        "    E3 --> F",
        "",
        '    F --> G["Job Normalization<br/>Standardize format"]',
        '    G --> H["SkillMatcher<br/>Calculate Match Scores"]',
        "",
        '    H --> I["Database Operations<br/>Duplicate Detection"]',
        '    I --> J{"Job Exists?"}',
        '    J -->|Yes| K["Update Existing Job"]',
        '    J -->|No| L["Create New Job"]',
        "",
        '    K --> M["Commit Transaction"]',
        "    L --> M",
        "",
        '    M --> N["Response Formatting<br/>JobListingResponse"]',
        '    N --> O["Return Results<br/>JobSearchResponse"]',
        "",
        "    style A fill:#e1f5ff",
        "    style D fill:#fff4e1",
        "    style H fill:#e1ffe1",
        "    style I fill:#ffe1f5",
        "    style O fill:#e1f5ff"
    ]
    
    mermaid_diagram = "\n".join(mermaid_lines)
    
    diagram = f"""# Job Search Pipeline Flow Diagram

**Generated:** {timestamp_str}

## Pipeline Overview

The job search pipeline processes requests from API endpoints through multiple stages to return matched and scored job listings.

## Flow Diagram

```mermaid
{mermaid_diagram}
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

"""
    
    return diagram


def main():
    """Main function to generate pipeline diagram."""
    print("=" * 80)
    print("PIPELINE FLOW DIAGRAM GENERATOR")
    print("=" * 80)
    print()
    
    print("Generating pipeline diagram...")
    diagram = generate_pipeline_diagram()
    
    # Save diagram
    output_file = BASE_DIR / "audit_pipeline_diagram.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(diagram)
    
    print(f"[OK] Pipeline diagram saved to: {output_file}")
    print()
    print("=" * 80)
    print("Diagram generation complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
