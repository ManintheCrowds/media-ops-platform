# Report Analysis Dashboard

**Generated:** 2025-12-25 18:00:44

---

## Executive Summary

This analysis consolidates findings from **39 reports** across the system.

### Key Metrics

- **Total Reports Analyzed:** 39
- **Total Size:** 470.73 KB
- **API Tests:** 34
- **Matcher Tests:** 22
- **Scraper Tests:** 3
- **Total Errors:** 26
- **Critical Issues:** 4
- **Recommendations:** 4

## Report Inventory

### By Type

| Type | Count |
|------|-------|
| data_inventory | 1 |
| other | 33 |
| status_report | 5 |

### By Extension

| Extension | Count |
|-----------|-------|
| .json | 9 |
| .md | 30 |

## Critical Issues Matrix

| Issue Category | Severity | Count | Description |
|----------------|----------|-------|-------------|
| API Tests | high | 7 | API endpoint test failures detected |
| Matcher Tests | high | 22 | Matcher test failures - average score: 0.211 |
| Scraper Tests | medium | 3 | Scraper test failures detected |
| Errors | high | 26 | Errors detected: {'result_error': 26} | Categories: {'endpoi... |

## Test Coverage Analysis

### API Tests

- **Total Endpoints Tested:** 198
- **Success Count:** 184
- **Failure Count:** 14
- **Success Rate:** 92.9%
- **Average Response Time:** 0.433s

### Matcher Tests

- **Total Tests:** 116
- **Pass Count:** 50
- **Fail Count:** 66
- **Pass Rate:** 43.1%
- **Average Score:** 0.211

### Task Status

- **Total Tasks:** 18
- **Completed:** 13
- **Pending:** 3
- **Failed:** 0
- **In Progress:** 2
- **Completion Rate:** 72.2%

## Success/Failure Rates by Component

### API Endpoints

| Endpoint | Success Rate | Avg Response Time |
|----------|-------------|-------------------|
| GET /api/v1/jobs | 100.0% | N/A |
| GET /api/v1/jobs/recommended?min_score=0.7&limit=10 | 100.0% | N/A |
| GET /api/v1/matching/stats | 100.0% | N/A |
| GET /health | 100.0% | N/A |
| POST /api/v1/jobs/search | 100.0% | N/A |
| POST /api/v1/matching/batch-score | 100.0% | N/A |
| POST /api/v1/matching/score | 100.0% | N/A |
| POST /api/v1/scheduler/start | 100.0% | N/A |
| POST /api/v1/scheduler/stop | 100.0% | N/A |

## Recommendations

Prioritized recommendations based on frequency and severity:

### 1. Matcher (high priority)

**Recommendation:** Review and fix skill matcher scoring algorithm - scores are too low

- **Evidence Count:** 1
- **Estimated Effort:** 4-6 hours

### 2. API (high priority)

**Recommendation:** Fix failing API endpoints or update tests

- **Evidence Count:** 1
- **Estimated Effort:** 2-3 hours

### 3. Errors (high priority)

**Recommendation:** Review and fix errors detected in test runs

- **Evidence Count:** 1
- **Estimated Effort:** 2-4 hours

### 4. Scrapers (medium priority)

**Recommendation:** Investigate scraper failures - may be due to anti-bot measures

- **Evidence Count:** 1
- **Estimated Effort:** 3-4 hours

## Inconsistencies Identified

Found **1** inconsistencies across reports:

- **inconsistent_results:** Task test-api-quick has inconsistent results across reports

## Timeline Summary

Total timeline entries: 65

| Timestamp | Task ID | Agent Type | Status | Duration (s) |
|-----------|---------|------------|--------|--------------|
| 2025-12-23T17:43:53 | test-api-quick | api_test | completed | 3.306 |
| 2025-12-23T17:43:53 | test-api-quick | api_test | completed | 3.306 |
| 2025-12-23T17:43:53 | test-api-quick | api_test | completed | 3.306 |
| 2025-12-23T17:43:53 | test-matcher-quick | matcher_test | completed | 0.023 |
| 2025-12-23T17:43:53 | test-matcher-quick | matcher_test | completed | 0.023 |
| 2025-12-23T17:43:53 | test-matcher-quick | matcher_test | completed | 0.023 |
| 2025-12-23T17:44:11 | test-single-api | api_test | completed | 2.473 |
| 2025-12-23T17:44:11 | test-single-api | api_test | completed | 2.473 |
| 2025-12-23T17:44:11 | test-single-api | api_test | completed | 2.473 |
| 2025-12-23T17:44:11 | test-single-api | api_test | completed | 2.473 |
| 2025-12-23T17:44:11 | test-single-api | api_test | completed | 2.473 |
| 2025-12-23T17:44:11 | test-single-api | api_test | completed | 2.473 |
| 2025-12-23T17:44:13 | test-multi-api-1 | api_test | completed | 2.117 |
| 2025-12-23T17:44:13 | test-multi-api-1 | api_test | completed | 2.117 |
| 2025-12-23T17:44:13 | test-multi-api-1 | api_test | completed | 2.117 |
| 2025-12-23T17:44:13 | test-multi-api-1 | api_test | completed | 2.117 |
| 2025-12-23T17:44:13 | test-multi-api-1 | api_test | completed | 2.117 |
| 2025-12-23T17:44:13 | test-multi-api-1 | api_test | completed | 2.117 |
| 2025-12-23T17:44:13 | test-multi-api-2 | api_test | completed | 2.192 |
| 2025-12-23T17:44:13 | test-multi-api-2 | api_test | completed | 2.192 |
| ... | ... | ... | ... | ... |
*(45 more entries)*

---

*This report was generated automatically by the audit system.*