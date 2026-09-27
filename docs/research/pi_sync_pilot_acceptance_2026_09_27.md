# Pi sync pilot acceptance — WSL (2026-09-27)

**Branch:** `cursor/pi-sync-pilot-acceptance-3e8c`  
**Base:** `main` @ `1e7eea4` (includes merged [#144](https://github.com/ManintheCrowds/media-ops-platform/pull/144) + [#145](https://github.com/ManintheCrowds/media-ops-platform/pull/145))  
**Host:** Ubuntu WSL (`DESKTOP-B5G9NA1`); Docker Engine not available — no compose live proof.

## Gate results

| Gate | Result | Evidence |
|---|---|---|
| Contract (HTTP sync check/request/download/complete) | **PASS** | `education-service/tests/unit/test_pi_sync_http_acceptance.py` (9 tests w/ service unit) |
| Ready-state (`has_updates` only ready+checksum) | **PASS** | same + `test_pi_sync_service.py` |
| Device auth (human JWT / wrong device rejected) | **PASS** | HTTP acceptance suite |
| Integrity (checksum mismatch before extract) | **PASS** | `pi-client/tests/test_sync_integrity.py` |
| Safe extract (path traversal) | **PASS** | `pi-client/tests/test_sync_safe_extract.py` |
| Capabilities discovery | **PASS** | `tests/integration/test_api_capabilities.py` |
| Nginx auth_limit + `/api/v1/pi/` | **PASS** | `tests/unit/test_nginx_pi_routes.py` |
| Live compose / physical Pi | **SKIP** | No Docker on this WSL distro |
| Offline UI cache wiring | **RESIDUAL** | Out of #144 scope |
| Cache encryption wired | **RESIDUAL** | CryptoManager still unused by storage |
| Org-membership authz beyond device JWT | **RESIDUAL** | Device JWT match only |

## Commands run

```bash
pytest tests/unit/test_nginx_pi_routes.py --noconftest --no-cov
SECURITY_SERVICE_URL= DATABASE_URL='postgresql+psycopg://…' \
  pytest tests/integration/test_api_capabilities.py --no-cov
cd pi-client && PYTHONPATH=. pytest tests/test_sync_integrity.py tests/test_sync_safe_extract.py --no-cov
cd education-service && JWT_SECRET_KEY='…' PYTHONPATH=. \
  pytest tests/unit/test_pi_sync_http_acceptance.py tests/unit/test_pi_sync_service.py --noconftest --no-cov
```

## Gap fixes in this pass

- SQLAlchemy Declarative reserved `metadata` attr → `extra_data` mapped to DB column `"metadata"` (models + services + Pydantic aliases) so education TestClient suites can create tables without SAWarning/conflict noise becoming hard failures on newer SQLAlchemy.

## Verdict

Track A sync contract from PR #144 is **acceptance-green on automated gates** for this WSL host. Residuals above remain for follow-on pilots.
