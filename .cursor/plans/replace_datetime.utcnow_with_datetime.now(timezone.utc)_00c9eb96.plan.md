---
name: Replace datetime.utcnow with datetime.now(timezone.utc)
overview: Replace all 99 instances of datetime.utcnow() calls and 9 instances of default=datetime.utcnow in SQLAlchemy models with timezone-aware datetime.now(timezone.utc) to ensure Python 3.12+ compatibility.
todos: []
---

# Replace datetime.

utcnow() with datetime.now(timezone.utc)

## Overview

This refactoring addresses the deprecation of `datetime.utcnow()` in Python 3.12+ by replacing all instances with `datetime.now(timezone.utc)`, which returns a timezone-aware datetime object.

## Scope

- **99 instances** of `datetime.utcnow()` function calls across the codebase
- **9 instances** of `default=datetime.utcnow` in SQLAlchemy model definitions
- **1 instance** of `onupdate=datetime.utcnow` in SQLAlchemy model definitions

## Files to Update

### Core Application Files

- `app/auth/jwt_handler.py` - 2 instances
- `app/api/health.py` - 8 instances

### Security Service Files

- `security-service/security_service/monitoring/alerting.py` - 5 instances
- `security-service/security_service/monitoring/log_aggregator.py` - 4 instances
- `security-service/security_service/monitoring/anomaly.py` - 4 instances
- `security-service/security_service/monitoring/ids.py` - 3 instances
- `security-service/security_service/compliance/reporting.py` - 2 instances
- `security-service/security_service/compliance/backup_verification.py` - 5 instances
- `security-service/security_service/compliance/audit.py` - 2 instances
- `security-service/security_service/protection/firewall.py` - 5 instances
- `security-service/security_service/protection/ddos.py` - 4 instances
- `security-service/security_service/intelligence/ip_reputation.py` - 5 instances
- `security-service/security_service/intelligence/vulnerability.py` - 3 instances
- `security-service/security_service/intelligence/patch_management.py` - 4 instances
- `security-service/security_service/intelligence/malware.py` - 2 instances
- `security-service/security_service/siem/engine.py` - 2 instances
- `security-service/security_service/siem/correlation.py` - 3 instances
- `security-service/security_service/siem/incidents.py` - 5 instances
- `security-service/security_service/main.py` - 1 instance

### Security Service Models (SQLAlchemy defaults)

- `security-service/security_service/models/security_events.py` - 1 default
- `security-service/security_service/models/incidents.py` - 2 defaults (1 default, 1 onupdate)
- `security-service/security_service/models/threats.py` - 6 defaults

### Education Service Files

- `education-service/app/services/pi_service.py` - 3 instances
- `education-service/app/services/security_service.py` - 3 instances
- `education-service/app/api/pi/iot.py` - 1 instance

### PI Client Files

- `pi-client/pi_client/security/certificates.py` - 4 instances
- `pi-client/pi_client/security/auth.py` - 2 instances
- `pi-client/pi_client/cache/storage.py` - 2 instances
- `pi-client/pi_client/cache/manager.py` - 2 instances
- `pi-client/pi_client/cache/sync.py` - 1 instance

### Test Files

- `tests/unit/test_auth_jwt.py` - 1 instance
- `tests/unit/test_models.py` - 1 instance
- `tests/integration/test_database.py` - 2 instances

## Implementation Strategy

### 1. Import Updates

For each file, update imports to include `timezone`:

- Change `from datetime import datetime, timedelta` to `from datetime import datetime, timedelta, timezone`
- Change `from datetime import datetime` to `from datetime import datetime, timezone`

### 2. Function Call Replacements

Replace all `datetime.utcnow()` calls with `datetime.now(timezone.utc)`:

- Direct calls: `datetime.utcnow()` → `datetime.now(timezone.utc)`
- In expressions: `datetime.utcnow() + timedelta(...)` → `datetime.now(timezone.utc) + timedelta(...)`
- In comparisons: `datetime.utcnow() >= renewal_date` → `datetime.now(timezone.utc) >= renewal_date`
- In method calls: `datetime.utcnow().isoformat()` → `datetime.now(timezone.utc).isoformat()`
- In method calls: `datetime.utcnow().timestamp()` → `datetime.now(timezone.utc).timestamp()`

### 3. SQLAlchemy Model Defaults

For SQLAlchemy model defaults, use lambda functions to ensure evaluation at runtime:

- `default=datetime.utcnow` → `default=lambda: datetime.now(timezone.utc)`
- `onupdate=datetime.utcnow` → `onupdate=lambda: datetime.now(timezone.utc)`

**Note**: SQLAlchemy requires callables for defaults to evaluate at insert/update time, not import time.

### 4. Compatibility Considerations

- Timezone-aware datetimes work correctly with `timedelta` operations
- Comparisons between timezone-aware and timezone-naive datetimes may raise warnings in Python 3.12+, but database fields using `DateTime(timezone=True)` are already timezone-aware
- Some models use `DateTime` without `timezone=True`; these should continue to work but may need future migration to `DateTime(timezone=True)`

## Testing Strategy

1. **Unit Tests**: Run all unit tests to verify functionality

- `pytest tests/unit/`
- Focus on `tests/unit/test_auth_jwt.py` which tests datetime operations

2. **Integration Tests**: Run integration tests

- `pytest tests/integration/`
- Verify database operations with datetime fields

3. **Manual Verification**: Check critical paths

- JWT token creation/verification
- Health check endpoints
- Security event logging
- Certificate validation

## Risk Assessment

**Risk Level**: Low to Medium**Rationale**:

- Straightforward find-and-replace operation
- Timezone-aware datetimes are compatible with existing code
- Database models already support timezone-aware datetimes
- Potential issues: Comparisons with timezone-naive datetimes in some edge cases

**Mitigation**:

- Comprehensive test coverage
- Careful review of datetime comparisons
- Verify all imports are updated correctly

## Rollback Plan

If issues arise:

1. Revert changes using git
2. All changes are in code files, no database migrations required
3. No configuration changes needed

## Verification Checklist

- [ ] All 99 instances of `datetime.utcnow()` replaced
- [ ] All 9 instances of `default=datetime.utcnow` replaced
- [ ] All 1 instance of `onupdate=datetime.utcnow` replaced
- [ ] All imports updated to include `timezone`
- [ ] All unit tests pass
- [ ] All integration tests pass