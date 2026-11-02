# Local-first Pi sync pilot acceptance — 2026-09-27 (WSL)

**Host:** Ubuntu WSL (`linux 6.18.33.2-microsoft-standard-WSL2`)  
**Checkout:** `media-ops-platform` branch `cursor/pi-sync-pilot-acceptance-3e8c`  
**Baseline:** `main` @ `1e7eea4` (includes PR #144 Track A+B, PR #145 setuptools CI)  
**Plan:** `docs/plans/2026-09-27-001-pi-sync-pilot-acceptance-plan.md`  
**Docker:** CLI present via Docker Desktop path but **not usable** in this distro (WSL integration inactive). Compose live stack = residual.

## Gate matrix

| Gate | Status | Evidence |
|---|---|---|
| Contract (check/request/download/complete) | **pass** | `education-service/tests/unit/test_pi_sync_http_acceptance.py` — happy path streams gzip + complete JSON |
| Ready-state (`has_updates`) | **pass** | Pending without checksum → `has_updates=false`; request materializes ready |
| Device authz (JWT) | **pass** | Human JWT → 403; wrong device → 403; matching device → 200; unauth → 401 |
| Integrity (checksum) | **pass** | `pi-client/tests/test_sync_integrity.py` — mismatch skips extract |
| Safe extract | **pass** | `pi-client/tests/test_sync_safe_extract.py` |
| Capabilities discovery | **pass** | `tests/integration/test_api_capabilities.py` |
| Nginx `/api/v1/pi/` + `auth_limit` | **pass** | `tests/unit/test_nginx_pi_routes.py` (static) |
| Offline UI from cache | **residual** | Out of #144 / this pilot scope |
| Secret / cache encryption | **residual** | Out of scope; non-sensitive pilot framing |
| Restart / resume download | **residual** | Not automated this pass |
| Compose live stack | **residual** | Enable Docker Desktop WSL integration, then smoke |
| Org-membership beyond device_id | **residual** | Device JWT match enforced; deeper org ACL not proven |

## Commands run (docker-free)

```bash
# education
cd education-service && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. \
  pytest tests/unit/test_pi_sync_service.py tests/unit/test_pi_sync_http_acceptance.py \
  -q -o addopts= --noconftest

# pi-client
cd pi-client && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. \
  pytest tests/test_sync_safe_extract.py tests/test_sync_integrity.py -q -o addopts=

# platform
cd . && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. \
  pytest tests/unit/test_nginx_pi_routes.py tests/integration/test_api_capabilities.py \
  -q -o addopts=
```

All three suites green on this host (9 + 5 + 4 tests).

## Gaps fixed during the pass (U4)

1. **SQLAlchemy reserved `metadata` attr** on education ORM models → renamed Python attr to `extra_data` (DB column still `metadata`); schemas accept both via `AliasChoices`.
2. **Sqlite-safe `create_engine`** in `education-service/app/database.py` and `app/database.py` (skip `pool_size`/`max_overflow` for sqlite).
3. **Platform test import** sets `DATABASE_URL=sqlite://` before app import in `tests/conftest.py`.
4. Education sync unit tests set `DATABASE_URL=sqlite://` for docker-free collection.

## Residuals / follow-ups

- Enable Docker Desktop ↔ WSL integration; optional compose smoke for nginx + education + platform.
- Offline content browser wiring (`pi-client` display server).
- Cache encryption or explicit non-sensitive pilot docs.
- Org-scoped authorization beyond matching `device_id` on device JWT.
- CI: ensure education unit tests run without Postgres (already sqlite-capable after this pass).

## Verdict

**Track A Pi sync pilot acceptance: PASS** on this WSL host for contract/auth/integrity/discovery/nginx-static gates. Live compose and offline UX remain residuals, not blockers for this LFG slice.
