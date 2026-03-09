# Job Application Automation Service

A comprehensive job search and application automation service that discovers, matches, and tracks job listings from multiple sources (Indeed, LinkedIn, Glassdoor, ZipRecruiter) with skills-based matching and AI-powered cover letter generation.

## Features

- **Multi-Source Job Search**: Scrapes jobs from Indeed, LinkedIn, Glassdoor, and ZipRecruiter
- **Skills-Based Matching**: Automatically scores jobs based on your skill profile
- **AI Cover Letter Generation**: Uses configurable LLM (Ollama local, OpenAI, or Anthropic) to generate personalized cover letters
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

**Optional Variables (LLM / Cover Letter):**
- `LLM_PROVIDER` - `ollama` (local), `openai`, or `anthropic` (default: ollama)
- `LLM_MODEL` - Model name (default: llama3.2). Examples: `llama3.2`, `mistral`, `gpt-4o`, `claude-3-5-sonnet`, `meta/llama-3.1-8b-instruct` (NIM)
- `OLLAMA_URL` - Ollama service URL when using local LLM (default: http://localhost:11434)
- `OPENAI_API_KEY` - Required when LLM_PROVIDER=openai (also used for NVIDIA NIM)
- `OPENAI_BASE_URL` - Base URL when using OpenAI-compatible API (e.g. NIM: https://integrate.api.nvidia.com/v1)
- `ANTHROPIC_API_KEY` - Required when LLM_PROVIDER=anthropic

**Docker:** When running via `docker compose up`, set NIM vars in `.env` at `job-automation-service/` or export before starting. The container will use NIM when `LLM_PROVIDER=openai` and `OPENAI_API_KEY` is set.

**Recommended local models:**

| Model | Size | Best for |
|-------|------|----------|
| llama3.2 | ~2GB | Fast, general purpose |
| mistral | ~4GB | Strong instruction following |

**Other optional variables:**
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

Cover letters are generated using a configurable LLM. Choose local (Ollama) or cloud (OpenAI, Anthropic) via `LLM_PROVIDER`.

**Local (Ollama):** Set `LLM_PROVIDER=ollama` (default). Make sure Ollama is running:

```bash
# Install Ollama (if not already installed)
# https://ollama.ai

# Pull a model (llama3.2 or mistral recommended)
ollama pull llama3.2

# Start Ollama (usually runs on port 11434)
```

**Cloud:** Set `LLM_PROVIDER=openai` or `LLM_PROVIDER=anthropic` and provide the corresponding API key.

The service redacts PII (email, phone, SSN) from job descriptions before sending to the LLM. It automatically generates personalized cover letters based on:
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

### LLM Cover Letter Workflow

Cover letter generation process:
1. PII (email, phone, SSN) redacted from job description
2. Prompt built with system + user messages (chat format)
3. LLM called via configured provider (Ollama, OpenAI, or Anthropic)
4. Cover letter formatted and returned
5. Fallback to template if LLM unavailable or returns empty

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

### LLM Setup

Cover letter generation uses the configured `LLM_PROVIDER`. For local (Ollama), ensure Ollama is running and the model is pulled. For cloud (OpenAI/Anthropic), set the corresponding API key. If the LLM is unavailable, the service falls back to a template-based cover letter.

### Database Migrations

Always run migrations after pulling updates:

```bash
alembic upgrade head
```

## Troubleshooting

### Docker build fails: Unable to connect (network)

The Dockerfile no longer uses `apt-get` (psycopg2-binary has wheels). If the build still fails, Docker cannot reach PyPI or other hosts. Check:

- **VPN**: Disconnect or allow Docker through VPN split-tunneling
- **Firewall**: Allow Docker Desktop / WSL2 outbound HTTP (80) and HTTPS (443)
- **Proxy**: If behind a corporate proxy, configure Docker daemon proxy settings
- **Connectivity tests**:
  - `docker run --rm alpine ping -c 2 8.8.8.8` — basic connectivity
  - `docker run --rm alpine wget -qO- https://pypi.org` — PyPI/HTTPS access

### pip install fails: pg_config not found (psycopg2-binary)

On Windows with Python 3.13, `psycopg2-binary==2.9.9` has no pre-built wheel and tries to build from source, which requires PostgreSQL dev tools (`pg_config`).

**Fix:** `requirements.txt` pins `psycopg2-binary>=2.9.11`, which has Python 3.13 Windows wheels. Ensure you have the latest requirements and run:

```bash
pip install -r requirements.txt
```

**If still failing:**
- **Option A (pre-built wheel only):** `pip install psycopg2-binary --only-binary :all:` then `pip install -r requirements.txt`
- **Option B (PostgreSQL dev tools):** Install [PostgreSQL for Windows](https://www.postgresql.org/download/windows/) and add its `bin` directory (contains `pg_config`) to `PATH`
- **Option C (Docker):** Use `docker-compose up` for the full stack; the container uses Python 3.11 with wheels

### Service won't start

- Check database connection: `DATABASE_URL` environment variable
- Verify PostgreSQL is running: `docker ps | grep job-automation-db`
- Check logs: `docker logs platform-job-automation`

### No jobs found

- Verify scrapers are working (check logs)
- Some sites may block automated access
- Try different search queries or locations

### Cover letters not generating

- **Ollama (local):** Verify Ollama is running: `curl http://localhost:11434/api/tags`; check `OLLAMA_URL`; ensure model is available: `ollama list`
- **OpenAI/Anthropic:** Verify `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set when `LLM_PROVIDER` is openai or anthropic
- Service falls back to template if LLM is unavailable

## License

This service integrates with the main self-hosted platform.

