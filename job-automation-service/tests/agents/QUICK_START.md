# Quick Start Guide - Agent Framework

## Prerequisites

1. **Database Migration Applied**
   ```bash
   cd job-automation-service
   $env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"
   alembic upgrade head
   ```

2. **Service Running** (for API tests)
   ```bash
   uvicorn app.main:app --reload --port 8004
   ```

## Quick Commands

### Run Quick Test Suite
```powershell
cd job-automation-service
python -m tests.agents.run_agents --suite quick
```

### Run Full Test Suite
```powershell
python -m tests.agents.run_agents --suite full
```

### Run Gap Analysis Only
```powershell
python -m tests.agents.run_agents --suite gap
```

### Run Specific Agents
```powershell
python -m tests.agents.run_agents --agents api_test matcher_test gap_analysis
```

### Validate Framework
```powershell
python -m tests.agents.validate_framework
```

## Using PowerShell Script

```powershell
# From job-automation-service directory
.\tests\agents\run_agents.ps1 --suite full --verbose
```

## View Reports

Reports are generated in `tests/agents/reports/`:
- Markdown: `report_YYYYMMDD_HHMMSS.md`
- JSON: `report_YYYYMMDD_HHMMSS.json`

## Common Issues

### ModuleNotFoundError
**Problem**: `No module named 'tests.agents'`

**Solution**: Run from `job-automation-service` directory:
```powershell
cd job-automation-service
python -m tests.agents.run_agents
```

### Database Connection Error
**Problem**: Cannot connect to database

**Solution**: Set DATABASE_URL:
```powershell
$env:DATABASE_URL = "postgresql://jobautomation:password@localhost:5433/jobautomation"
```

### Service Not Running
**Problem**: API tests fail with connection errors

**Solution**: Start the service:
```powershell
uvicorn app.main:app --reload --port 8004
```

## Agent Types

### Testing Agents
- `scraper_test` - Test job scrapers
- `matcher_test` - Test skills matching
- `api_test` - Test API endpoints
- `cover_letter_test` - Test cover letter generation
- `scheduler_test` - Test scheduler

### Analysis Agents
- `gap_analysis` - Identify missing features
- `performance_analysis` - Analyze performance
- `security_analysis` - Security checks
- `doc_analysis` - Documentation analysis
- `compliance_analysis` - Compliance checks

## Next Steps

1. Review generated reports in `tests/agents/reports/`
2. Check framework documentation: `docs/AGENT_FRAMEWORK.md`
3. Customize agents or create new ones as needed

