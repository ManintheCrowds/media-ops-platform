# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a Python/FastAPI self-hosted platform that provides unified management of home lab services (file storage, media, git, monitoring, security, etc.) with SSO, service registry, API gateway, and a web dashboard.

### Required Environment Variables

The platform **will not start** without these set (minimum 32 characters each):
- `SECRET_KEY`
- `JWT_SECRET_KEY`

Also required for full functionality:
- `DATABASE_URL` — defaults to `postgresql://platform:platform@postgres:5432/platform`; use `postgresql://platform:platform@localhost:5432/platform` when running outside Docker
- `DEBUG=True` for development mode

### Running Services

**PostgreSQL** (required):
```bash
docker compose up -d postgres
```
Wait for it to become healthy before starting the API.

**Platform API** (dev mode with hot-reload):
```bash
DATABASE_URL="postgresql://platform:platform@localhost:5432/platform" \
SECRET_KEY="<32+ char secret>" \
JWT_SECRET_KEY="<32+ char secret>" \
DEBUG=True \
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Database initialization** (first time only):
```python
python3 -c "from app.database import init_db; init_db()"
```

### Lint / Test / Build

See `README.md` and `.github/workflows/tests.yml` for full CI commands. Key commands:

- **Lint**: `flake8 app services --count --select=E9,F63,F7,F82 --show-source --statistics`
- **Format check**: `black --check app services tests`
- **Type check**: `mypy app --ignore-missing-imports || true`
- **Unit tests**: `pytest tests/unit -v -m "unit"`
- **Integration tests**: `pytest tests/integration -v -m "integration"` (needs PostgreSQL)
- **E2E tests**: `pytest tests/e2e -v -m "e2e"`
- **All tests**: `pytest`

### Gotchas

- `requirements.txt` has a dependency conflict: `fastapi>=0.128.0` needs `pydantic>=2.7.0` but the file pins `pydantic==2.5.0`. Workaround: install without the strict pydantic pin (let pip resolve to a compatible version).
- The `arlo` git dependency (`arlo @ git+https://github.com/jeffreydwalter/arlo.git`) is for optional camera integration. It can be skipped without affecting core functionality or most tests.
- Some API routes (e.g. `/api/services`, `/api/health`) require a trailing slash or `curl -L` to follow 307 redirects.
- Tests use SQLite in-memory (see `tests/conftest.py`) and set their own `SECRET_KEY`/`JWT_SECRET_KEY`, so they run without PostgreSQL.
- The `pytest.ini` enforces `--cov-fail-under=70` by default. For targeted test runs (e.g. `pytest tests/unit -m unit`), coverage is calculated on the subset and may fall below 70%.
- Docker socket may need permission fix: `sudo chmod 666 /var/run/docker.sock` after starting the Docker daemon.
