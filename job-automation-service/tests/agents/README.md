# Multi-Agent Testing and Gap Analysis Framework

## Quick Start

### Prerequisites

1. Database migration applied:
   ```bash
   alembic upgrade head
   ```

2. Service running (for API tests):
   ```bash
   uvicorn app.main:app --reload
   ```

### Running Agents

**Basic usage:**
```bash
# Full test suite
python -m tests.agents.run_agents

# Quick test suite
python -m tests.agents.run_agents --suite quick

# Specific agents
python -m tests.agents.run_agents --agents api_test matcher_test

# With custom parallel limit
python -m tests.agents.run_agents --max-parallel 5
```

**Using PowerShell:**
```powershell
.\tests\agents\run_agents.ps1 --suite full --verbose
```

**Using Bash:**
```bash
./tests/agents/run_agents.sh --suite quick
```

### Validation

Run validation tests:
```bash
python -m tests.agents.validate_framework
```

## Reports

Reports are generated in `tests/agents/reports/`:
- `report_YYYYMMDD_HHMMSS.md` - Markdown report
- `report_YYYYMMDD_HHMMSS.json` - JSON report

## Documentation

See [AGENT_FRAMEWORK.md](../docs/AGENT_FRAMEWORK.md) for complete documentation.

