# Coding Standards Matrix

**Purpose**: Lookup table for AI agents. Consult before generating code.

**How to Use**: Before writing code, identify relevant domain(s), look up standards and reference implementations, then generate.

**Related Documents**:
- [AI_PATTERNS.md](AI_PATTERNS.md) - Code implementation patterns
- [AI_CODEBASE_MAP.md](AI_CODEBASE_MAP.md) - File locations and structure
- [AI_PROMPT_LIBRARY.md](AI_PROMPT_LIBRARY.md) - Prompt templates

---

## Table 1: Standards by Domain

| Domain | Standard | Description | Reference |
|--------|----------|-------------|-----------|
| Python style | PEP 8 | Formatting rules | https://peps.python.org/pep-0008/ |
| Python typing | PEP 484 | Type hints | https://peps.python.org/pep-0484/ |
| API design | OpenAPI 3.1 | REST schema design | https://spec.openapis.org/oas/v3.1.0 |
| Web security | OWASP Top 10 | Web security risks | https://owasp.org/www-project-top-ten/ |
| Container security | CIS Docker Benchmark | Secure container configs | https://www.cisecurity.org/benchmark/docker |
| Database design | PostgreSQL docs | Indexing, normalization | https://www.postgresql.org/docs/current/ |
| Python linting | Ruff rules | Static analysis | https://docs.astral.sh/ruff/ |
| SQL migrations | Alembic | Schema migration practices | https://alembic.sqlalchemy.org/ |
| Async Python | PEP 492 (asyncio) | Async patterns | https://peps.python.org/pep-0492/ |

---

## Table 2: Pattern to Reference Implementation

| Pattern | Internal Reference | External Reference |
|---------|-------------------|---------------------|
| Service Client | [AI_PATTERNS.md](AI_PATTERNS.md) §1; `services/file_storage/seafile_client.py`, `services/media_server/jellyfin_client.py` | [encode/httpx](https://github.com/encode/httpx) |
| FastAPI + Auth | [AI_PATTERNS.md](AI_PATTERNS.md) §2; `app/api/gateway.py`, `app/auth/oauth2.py` | [tiangolo/full-stack-fastapi-postgresql](https://github.com/tiangolo/full-stack-fastapi-postgresql) |
| API design | [AI_PATTERNS.md](AI_PATTERNS.md) §2 | [encode/starlette](https://github.com/encode/starlette) |
| Database models | [AI_PATTERNS.md](AI_PATTERNS.md) §3; `app/models/` | [sqlalchemy/sqlalchemy](https://github.com/sqlalchemy/sqlalchemy), [alembic/alembic](https://github.com/alembic/alembic) |
| Configuration | [AI_PATTERNS.md](AI_PATTERNS.md) §6; `app/config.py`, `services/*/config.py` | [pydantic/pydantic-settings](https://github.com/pydantic/pydantic-settings) |
| Testing | [AI_PATTERNS.md](AI_PATTERNS.md) §4; `tests/` | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) |
| Docker / Compose | `docker-compose.yml`, `nginx/` | [docker/awesome-compose](https://github.com/docker/awesome-compose) |

---

## See Also

- [AI Patterns](AI_PATTERNS.md) - Code implementation patterns
- [AI Codebase Map](AI_CODEBASE_MAP.md) - Navigation guide
- [AI Prompt Library](AI_PROMPT_LIBRARY.md) - Reusable prompt templates

---

## Maintenance

- **Last link audit:** 2026-03-07 (run `markdown-link-check` or manual)
- **Update trigger:** New standards or reference repos; quarterly link check
