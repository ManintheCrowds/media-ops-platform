# API documentation — software

## Archivist / transcription services

Archivist runs as containerized workers (ingest → WhisperX → SCC captions → publish). Operational runbooks live under `docs/` and `portfolio/`; no single public OpenAPI for the full municipal pipeline in this tree.

## Self-hosted platform API

**Stack:** FastAPI, PostgreSQL, OAuth2/JWT, Docker Compose.

| Surface | Location |
|---------|----------|
| Interactive OpenAPI | `http://localhost:8000/docs` when Platform API is up (see root README Quick start) |
| Health | `GET /health` (and service-registry routes per deployment) |
| Gateway | Unified entry for registered homelab services |

Clone and start:

```bash
docker compose up -d
# Platform API typically on port 8000 — confirm in docker-compose.yml / README
```

For route-level detail, open **Swagger UI** at `/docs` after `docker compose up` or read `platform-api/` source modules.

## Security

- Never commit `.env`; use `.env.example` as the variable checklist.
- Run gitleaks / CI security workflows before changing repo visibility to public.
