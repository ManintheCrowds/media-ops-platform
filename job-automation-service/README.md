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

### Environment Variables

The service uses environment variables for configuration. Create a `.env` file in the service root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your actual credentials
nano .env
```

**Required Variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `ADZUNA_API_ID` - Adzuna API ID (get from https://developer.adzuna.com/)
- `ADZUNA_API_KEY` - Adzuna API key
- `JSEARCH_API_KEY` - JSearch API key (get from https://jsearch.app/)

**Optional Variables:**
- `OLLAMA_URL` - Ollama service URL (default: http://localhost:11434)
- `OLLAMA_MODEL` - Model name (default: llama2)
- `DEFAULT_LOCATION` - Default search location (default: Minneapolis, MN)
- `SECRET_KEY` - Application secret key (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)

**Security Note:** Never commit `.env` files to version control. The `.env` file is already in `.gitignore`.

See [CREDENTIAL_MANAGEMENT.md](../CREDENTIAL_MANAGEMENT.md) for detailed credential management guidelines.

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

## Architecture

### Scraper Architecture

The service uses a modular scraper architecture:
- **Base Scraper**: Common scraping utilities and base class
- **Source-Specific Scrapers**: Indeed, LinkedIn, Glassdoor, ZipRecruiter
- **Rate Limiting**: Per-source rate limiting to respect ToS
- **Error Handling**: Retry logic and graceful degradation
- **Data Normalization**: Standardized job data format across sources

### Matching Algorithm

Skills-based matching uses:
- **Skill Extraction**: Parses job descriptions for required skills
- **Skill Matching**: Compares job requirements with user skill profile
- **Proficiency Weighting**: Higher proficiency = better match score
- **Experience Weighting**: More years of experience = higher score
- **Composite Scoring**: Combines multiple factors for final match score

### Ollama Integration Workflow

Cover letter generation process:
1. Job description and user profile sent to Ollama
2. LLM generates personalized cover letter
3. Cover letter formatted and returned
4. Optionally saved with application
5. Fallback to template if Ollama unavailable

## Platform Integration

The job automation service integrates with the main platform:

- **Service Registry**: Registers with platform API
- **Authentication**: Uses platform JWT tokens for API access
- **Health Monitoring**: Exposes health endpoint for platform monitoring
- **Metrics**: Prometheus metrics available to monitoring stack

### Service Registration

Register the job automation service with the platform:

```bash
curl -X POST http://localhost:8000/api/services \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "job-automation-service",
    "service_type": "automation",
    "base_url": "http://job-automation-service:8004",
    "health_check_url": "http://job-automation-service:8004/health",
    "requires_auth": true
  }'
```

### Authentication Flow

1. User authenticates with platform API
2. Platform returns JWT token
3. Token used for job automation API requests
4. Service validates token with platform
5. Authorized requests processed

## Related Services

- [Platform API](../README.md) - Main integration layer
- [Monitoring Stack](../monitoring/README.md) - Prometheus, Grafana

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

