# Coverage Gaps Summary

**Generated:** 2026-06-24 (Session A — test health closure)  
**Total Coverage:** 78.98% (Target: 70%) — **gate met; all unit tests green**  
**Unit tests:** 457 passed, 0 failed, 0 errors (`pytest tests/unit -m unit --cov-fail-under=70`)  
**Scope:** `app/` + `services/` (`services/camera/arlo_module.py` omitted — integration-heavy; see `coverage.ini`)  
**Files Analyzed:** 34 modules in app/ and services/

## Top 10 Files with <70% Coverage

| File | Coverage % | Priority |
|------|------------|----------|
| `app/api/scheduler.py` | 49% | MEDIUM |
| `app/auth/oauth2.py` | 49% | MEDIUM |
| `services/camera/arlo_service.py` | 55% | LOW (omitted sibling `arlo_module.py`) |
| `app/api/camera.py` | 59% | MEDIUM (API integration) |
| `app/api/gateway.py` | 59% | MEDIUM (API integration) |
| `app/api/encoder.py` | 64% | MEDIUM |
| `app/config_base.py` | 74% | LOW |
| `services/monitoring/config.py` | 85% | LOW |
| `services/productivity/wiki_client.py` | 86% | LOW |
| `services/video_encoder/encoder_service.py` | 95% | LOW |

## Session A improvements (2026-06-24)

- **Test health:** in-memory SQLite fixture (`StaticPool`); encoder discover aiohttp mocks aligned; exception handler order fixed in `wiki_client` / `prometheus_client` (`TimeoutException` before `HTTPError`).
- **Coverage nibbles:** extended `test_coverage_gap_wiki_client.py`; `test_coverage_gap_aja_client.py` at 100%; new `test_coverage_gap_service_configs.py`; `prometheus_client` timeout path covered.

## Completed gap tests

| Test file | Target module |
|-----------|---------------|
| `tests/unit/test_coverage_gap_dashboard.py` | `services/monitoring/dashboard.py` |
| `tests/unit/test_coverage_gap_database.py` | `app/database.py` |
| `tests/unit/test_coverage_gap_prometheus_client.py` | `services/monitoring/prometheus_client.py` |
| `tests/unit/test_coverage_gap_vaultwarden_client.py` | `services/security/vaultwarden_client.py` |
| `tests/unit/test_coverage_gap_grafana_client.py` | `services/monitoring/grafana_client.py` |
| `tests/unit/test_coverage_gap_gitea_client.py` | `services/dev_tools/gitea_client.py` |
| `tests/unit/test_coverage_gap_wiki_client.py` | `services/productivity/wiki_client.py` |
| `tests/unit/test_coverage_gap_aja_client.py` | `services/video_encoder/aja_client.py` |
| `tests/unit/test_coverage_gap_base_service.py` | `services/base.py` |
| `tests/unit/test_coverage_gap_seafile_client.py` | `services/file_storage/seafile_client.py` |
| `tests/unit/test_coverage_gap_jellyfin_client.py` | `services/media_server/jellyfin_client.py` |
| `tests/unit/test_coverage_gap_health_api.py` | `app/api/health.py` |
| `tests/unit/test_coverage_gap_services_api.py` | `app/api/services.py` |
| `tests/unit/test_coverage_gap_main.py` | `app/main.py` |
| `tests/unit/test_coverage_gap_service_configs.py` | `services/*/config.py` validators |
| `tests/unit/test_coverage_gap_camera_api.py` | `app/api/camera.py` |
| `tests/unit/test_coverage_gap_encoder_api.py` | `app/api/encoder.py` |
| `tests/unit/test_coverage_gap_gateway_api.py` | `app/api/gateway.py` |

## Next steps (optional, post-gate)

1. Raise `app/api/scheduler.py` and `app/auth/oauth2.py` coverage if chasing 85%+.
2. Re-enable CI `--cov-fail-under=70` in `.github/workflows/tests.yml` after PF-REPO-6 billing is resolved.
3. Consider dedicated integration tests for `arlo_module.py` rather than unit-coverage chase.
