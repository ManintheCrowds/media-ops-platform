# Job Application Automation Service

A comprehensive job search and application automation service that discovers, matches, and tracks job listings from multiple sources (Indeed, LinkedIn, Glassdoor, ZipRecruiter) with skills-based matching and AI-powered cover letter generation.

## Features

- **Multi-Source Job Search**: Scrapes jobs from Indeed, LinkedIn, Glassdoor, and ZipRecruiter
- **Skills-Based Matching**: Automatically scores jobs based on your skill profile
- **AI Cover Letter Generation**: Uses local LLM (Ollama) to generate personalized cover letters
- **Application Tracking**: Track application status, follow-ups, and notes
- **Scheduled Searches**: Automated daily/weekly job searches
- **RESTful API**: Complete API for job search, matching, and application management

## Quick Start

### Prerequisites

- Docker and Docker Compose
- PostgreSQL 15+ (included in Docker setup)
- Ollama (for cover letter generation) - optional, can run separately

### Installation

1. **Start the service with Docker Compose:**

```bash
cd job-automation-service
docker-compose up -d
```

Or use the main platform docker-compose:

```bash
docker-compose up -d job-automation-service job-automation-db
```

2. **Run database migrations:**

```bash
# From the job-automation-service directory
cd job-automation-service
alembic upgrade head

# Or using Docker (if service is running)
docker exec -it platform-job-automation alembic upgrade head
```

3. **Initialize skill profile:**

```bash
# From the job-automation-service directory
cd job-automation-service
python scripts/init_skill_profile.py

# Or using Docker (if service is running)
docker exec -it platform-job-automation python scripts/init_skill_profile.py
```

4. **Access the service:**

- API: http://localhost:8004
- Docs: http://localhost:8004/docs
- Health: http://localhost:8004/health

## Configuration

Set environment variables in `.env` or docker-compose:

```bash
DATABASE_URL=postgresql://jobautomation:password@job-automation-db:5432/jobautomation
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2
DEFAULT_LOCATION=Minneapolis, MN
```

## API Endpoints

### Job Search

- `POST /api/v1/jobs/search` - Search jobs across multiple sources
- `GET /api/v1/jobs` - List saved jobs (with filtering)
- `GET /api/v1/jobs/{id}` - Get job details
- `GET /api/v1/jobs/recommended` - Get top matched jobs
- `POST /api/v1/jobs/{id}/refresh` - Re-scrape a job

### Applications

- `POST /api/v1/applications` - Create new application
- `GET /api/v1/applications` - List applications
- `GET /api/v1/applications/{id}` - Get application details
- `PATCH /api/v1/applications/{id}` - Update application
- `POST /api/v1/applications/{id}/followup` - Schedule follow-up
- `GET /api/v1/applications/pending-followups` - Get pending follow-ups

### Matching

- `POST /api/v1/matching/score` - Score a job description
- `POST /api/v1/matching/batch-score` - Score multiple jobs
- `GET /api/v1/matching/stats` - Get matching statistics

### Scheduler

- `POST /api/v1/scheduler/search` - Trigger manual search
- `POST /api/v1/scheduler/daily` - Trigger daily search
- `POST /api/v1/scheduler/weekly` - Trigger weekly search

## Usage Examples

### Search for Jobs

```bash
curl -X POST "http://localhost:8004/api/v1/jobs/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python developer",
    "location": "Minneapolis, MN",
    "sources": ["indeed", "linkedin"],
    "min_match_score": 0.7,
    "limit": 25
  }'
```

### Create Application with Cover Letter

```bash
curl -X POST "http://localhost:8004/api/v1/applications?generate_cover_letter=true" \
  -H "Content-Type: application/json" \
  -d '{
    "job_listing_id": 1,
    "status": "pending",
    "notes": "Interested in this role"
  }'
```

### Get Recommended Jobs

```bash
curl "http://localhost:8004/api/v1/jobs/recommended?min_score=0.7&limit=20"
```

## Skill Profile

The service uses a skill profile based on your resume. Skills are stored in the database with proficiency levels (1-5) and experience years. Initialize your profile:

```bash
# From job-automation-service directory
cd job-automation-service
python scripts/init_skill_profile.py

# Or using Docker
docker exec -it platform-job-automation python scripts/init_skill_profile.py
```

Skills are automatically matched against job descriptions to calculate match scores.

## Cover Letter Generation

Cover letters are generated using Ollama (local LLM). Make sure Ollama is running:

```bash
# Install Ollama (if not already installed)
# https://ollama.ai

# Pull a model
ollama pull llama2

# Start Ollama (usually runs on port 11434)
```

The service will automatically generate personalized cover letters based on:
- Job title and company
- Key requirements from job description
- Your relevant skills and experience

## Scheduled Searches

Set up automated job searches using cron or a task scheduler:

```bash
# Daily search (via API)
curl -X POST "http://localhost:8004/api/v1/scheduler/daily"

# Weekly search
curl -X POST "http://localhost:8004/api/v1/scheduler/weekly"
```

Or use a cron job:

```cron
0 9 * * * curl -X POST http://localhost:8004/api/v1/scheduler/daily
```

## Development

### Local Development

1. **Navigate to service directory:**

```bash
cd job-automation-service
```

2. **Create virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Set up database:**

```bash
# Start PostgreSQL
docker-compose up -d job-automation-db

# Run migrations (from job-automation-service directory)
alembic upgrade head

# Initialize skill profile (from job-automation-service directory)
python scripts/init_skill_profile.py
```

4. **Run the service:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
pytest tests/
```

## Project Structure

```
job-automation-service/
├── app/
│   ├── api/              # API endpoints
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── utils/            # Utility functions
├── alembic/              # Database migrations
├── scripts/             # Utility scripts
├── tests/               # Test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Important Notes

### Legal & ToS Compliance

- **Web Scraping**: Some job sites may prohibit automated scraping. Use APIs where available.
- **Rate Limiting**: The service includes rate limiting to be respectful of target sites.
- **LinkedIn**: LinkedIn has strict ToS. Consider using their official API for production.

### Ollama Setup

Cover letter generation requires Ollama. If Ollama is not available, the service will skip cover letter generation but continue to function.

### Database Migrations

Always run migrations after pulling updates:

```bash
alembic upgrade head
```

## Troubleshooting

### Service won't start

- Check database connection: `DATABASE_URL` environment variable
- Verify PostgreSQL is running: `docker ps | grep job-automation-db`
- Check logs: `docker logs platform-job-automation`

### No jobs found

- Verify scrapers are working (check logs)
- Some sites may block automated access
- Try different search queries or locations

### Cover letters not generating

- Verify Ollama is running: `curl http://localhost:11434/api/tags`
- Check `OLLAMA_URL` environment variable
- Ensure model is available: `ollama list`

## License

This service integrates with the main self-hosted platform.

