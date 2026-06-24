# Coverage Gaps Summary

**Generated:** 2026-06-24  
**Total Coverage:** 74.01% (Target: 70%) — **gate met**  
**Scope:** `app/` + `services/` (`services/camera/arlo_module.py` omitted — integration-heavy; see `coverage.ini`)  
**Files Analyzed:** 34 modules in app/ and services/

## Top 10 Files with <70% Coverage

| File | Coverage % | Untested Lines | Priority |
|------|------------|----------------|----------|
| `app/api/camera.py` | 46% | 106 | MEDIUM (API integration) |
| `app/api/gateway.py` | 26% | 106 | MEDIUM (API integration) |
| `app/api/encoder.py` | 45% | 65 | MEDIUM |
| `app/auth/oauth2.py` | 49% | 71 | MEDIUM |
| `services/productivity/wiki_client.py` | 67% | 36 | LOW |
| `services/camera/arlo_service.py` | 55% | 121 | LOW (omitted sibling `arlo_module.py`) |
| `app/api/scheduler.py` | 49% | 46 | MEDIUM |
| `app/api/health.py` | 26% → improved | partial | LOW |
| `app/api/services.py` | 49% → improved | partial | LOW |
| `services/dev_tools/gitea_client.py` | 56% → improved | partial | LOW |

## Completed gap tests (2026-06-24)

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

## Next steps (optional, post-gate)

1. Raise API route coverage (`camera`, `gateway`, `encoder`) with FastAPI client tests.
2. Re-enable CI `--cov-fail-under=70` in `.github/workflows/tests.yml` after PF-REPO-6 billing is resolved.
3. Consider dedicated integration tests for `arlo_module.py` rather than unit-coverage chase.
