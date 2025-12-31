# Coverage Gaps Summary

**Generated:** 2025-12-31  
**Total Coverage:** 58.38% (Target: 70%)  
**Files Analyzed:** 35 files in app/ and services/

## Top 10 Files with <70% Coverage

| File | Coverage % | Untested Lines | Priority |
|------|------------|----------------|----------|
| `services/monitoring/dashboard.py` | 0% | 28 | HIGH |
| `services/camera/arlo_module.py` | 1% | 533 | LOW (too large) |
| `services/video_encoder/aja_client.py` | 37% | 64 | MEDIUM |
| `services/productivity/wiki_client.py` | 39% | 69 | MEDIUM |
| `services/dev_tools/gitea_client.py` | 49% | 40 | MEDIUM |
| `services/monitoring/prometheus_client.py` | 53% | 30 | HIGH |
| `services/security/vaultwarden_client.py` | 52% | 28 | HIGH |
| `app/database.py` | 53% | 8 | HIGH |
| `services/monitoring/grafana_client.py` | 56% | 28 | HIGH |
| `services/camera/arlo_service.py` | 56% | 116 | MEDIUM |

## Top 5 Priority Gaps for Testing

### 1. `services/monitoring/dashboard.py` (0% coverage, 28 lines)
**Untested Functions:**
- `MonitoringDashboard.__init__()` - Constructor
- `MonitoringDashboard.get_system_metrics()` - CPU, memory, disk metrics
- `MonitoringDashboard.get_service_status()` - Service health aggregation

**Reason:** Completely untested, small file, high impact for monitoring

### 2. `app/database.py` (53% coverage, 8 missed lines)
**Untested Functions:**
- `get_db()` - Lines 23-27 (exception handling)
- `init_db()` - Lines 33-37 (database initialization)

**Reason:** Core utility, very small, critical for app functionality

### 3. `services/monitoring/prometheus_client.py` (53% coverage, 30 missed lines)
**Untested Functions:**
- `PrometheusClient.ping()` - Lines 33-34 (error handling)
- `PrometheusClient.query()` - Lines 39-40, 49-51 (session management, error handling)
- `PrometheusClient.query_range()` - Lines 55-57, 71-73 (session management, error handling)
- `PrometheusClient.get_targets()` - Lines 77-79, 85-87 (session management, error handling)
- `PrometheusClient.get_metrics()` - Lines 97-99 (error handling)

**Reason:** Service layer, manageable size, important for monitoring

### 4. `services/security/vaultwarden_client.py` (52% coverage, 28 missed lines)
**Untested Functions:**
- `VaultwardenClient.ping()` - Lines 39-40 (error handling)
- `VaultwardenClient.get_users()` - Lines 44-46, 52-54 (session management, error handling)
- `VaultwardenClient.get_user()` - Lines 58-60, 66-68 (session management, error handling)
- `VaultwardenClient.get_stats()` - Lines 72-74, 80-82 (session management, error handling)

**Reason:** Service layer, small file, security-related

### 5. `services/monitoring/grafana_client.py` (56% coverage, 28 missed lines)
**Untested Functions:**
- `GrafanaClient.ping()` - Lines 46-47 (error handling)
- `GrafanaClient.get_dashboards()` - Lines 52-53, 59-61 (session management, error handling)
- `GrafanaClient.get_dashboard()` - Lines 65-67, 73-75 (session management, error handling)
- `GrafanaClient.get_datasources()` - Lines 79-81, 87-89 (session management, error handling)

**Reason:** Service layer, small file, monitoring integration

## Next Steps

Create targeted test files for the top 3 priority gaps:
1. `tests/unit/test_coverage_gap_dashboard.py`
2. `tests/unit/test_coverage_gap_database.py`
3. `tests/unit/test_coverage_gap_prometheus_client.py`

