# API documentation — media-ops-platform

## CaptionPipeline / transcription services

CaptionPipeline workers (ingest → WhisperX → SCC → publish) are **not** in this clone. Case-study copy lives under `docs/portfolio/`; no public OpenAPI documents that pipeline here.

## Self-hosted platform API

**Stack:** FastAPI, PostgreSQL, OAuth2/JWT, Docker Compose.

| Surface | Location |
|---------|----------|
| Interactive OpenAPI | `http://localhost:8000/docs` when Platform API is up (see root README Quick start) |
| Health | `GET /api/health` (and service-registry routes per deployment) |
| Gateway | Unified entry for registered homelab services |

Clone and start:

```bash
docker compose up -d
# Platform API typically on port 8000 — confirm in docker-compose.yml / README
```

For route-level detail, open **Swagger UI** at `/docs` after `docker compose up` or read platform API source under `app/` and `services/`.

## Security

- Never commit `.env`; use `.env.example` as the variable checklist.
- Run gitleaks / CI security workflows on changes; this GitHub repo is already public.
