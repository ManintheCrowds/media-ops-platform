# AI Validation Checklist - Pre-Execution Validation

**Purpose**: Comprehensive pre-execution validation checklists for various types of tasks to ensure safety, completeness, and quality before any change is executed.

**How to Use Checklists**: 
- Complete the relevant checklist section before executing your task
- Use risk-level specific checklists for additional requirements
- Stop execution if any critical item fails validation

**Risk-Based Validation**: Checklists are organized by task type and risk level. Higher risk tasks require more validation steps.

**Related Documents**:
- [AI_TASK_TEMPLATES.md](AI_TASK_TEMPLATES.md) - Task decomposition with validation requirements
- [AI_PRINCIPLES.md](AI_PRINCIPLES.md) - Core principles including risk-tiered operations
- [AI_PROMPT_LIBRARY.md](AI_PROMPT_LIBRARY.md) - Validation prompt templates

---

## Section 1: Pre-Task Validation (Universal)

Complete this section for **every task**, regardless of type or risk level.

### Task Decomposition Check

- [ ] Task broken down into subtasks
- [ ] Dependencies identified and documented
- [ ] Parallelization opportunities identified
- [ ] Estimated time for each subtask

### Risk Level Assignment

- [ ] Risk level assigned: `[ ] LOW  [ ] MEDIUM  [ ] HIGH  [ ] CRITICAL`
- [ ] Risk level justification documented
- [ ] Risk level appropriate for task type

### Rollback Plan Creation

- [ ] Rollback plan documented
- [ ] Rollback steps are clear and executable
- [ ] Rollback tested (for HIGH/CRITICAL risk)

### Human Approval

- [ ] Approval obtained (if required by risk level):
  - LOW: Single reviewer
  - MEDIUM: Two reviewers
  - HIGH: Lead approval
  - CRITICAL: Team consensus

### Backup Requirements

- [ ] Backups created (if required by risk level):
  - LOW: Git commit sufficient
  - MEDIUM: Git tag + database backup
  - HIGH: Full system backup
  - CRITICAL: Multiple backups + staging test

### Git Tag Requirements

- [ ] Git tag created (if required by risk level):
  - LOW: Not required
  - MEDIUM: Required
  - HIGH: Required
  - CRITICAL: Required

### Dependency Verification

- [ ] All dependencies available
- [ ] External services accessible
- [ ] Required tools installed
- [ ] Configuration valid

---

## Section 2: Code Change Validation

### Before Writing Code

- [ ] **Pattern Identification**: Appropriate pattern identified from [AI_PATTERNS.md](AI_PATTERNS.md)
- [ ] **Existing Code Review**: Similar code reviewed for consistency
- [ ] **Type Hints Planning**: Type hints planned for all functions
- [ ] **Error Handling Planning**: Error handling strategy defined
- [ ] **Test Planning**: Test strategy defined (unit, integration, e2e)

### During Code Writing

- [ ] **Pattern Compliance**: Code follows patterns from [AI_PATTERNS.md](AI_PATTERNS.md)
- [ ] **Type Hints Added**: All functions have type hints
- [ ] **Docstrings Added**: All public functions have docstrings
- [ ] **Error Handling Implemented**: Appropriate error handling in place
- [ ] **No Hardcoded Values**: All values come from configuration

### After Code Writing

- [ ] **Formatting**: Code formatted with Black: `black {file}`
- [ ] **Linting**: Code passes flake8: `flake8 {file}`
- [ ] **Type Checking**: Code passes mypy: `mypy {file}`
- [ ] **Tests Written**: Tests written for new code
- [ ] **Tests Pass**: All tests pass: `pytest`
- [ ] **Documentation Updated**: Documentation updated if needed

---

## Section 3: Service Integration Validation

### Before Integration

- [ ] **API Review**: Service API documentation reviewed
- [ ] **Health Endpoint**: Health check endpoint identified
- [ ] **Auth Method**: Authentication method understood
- [ ] **Environment Variables**: Required environment variables documented
- [ ] **Docker Image**: Docker image available and tested
- [ ] **Network Requirements**: Network requirements understood

### During Integration

- [ ] **Config Class**: Configuration class created following pattern
- [ ] **Client Class**: Service client class created following pattern
- [ ] **Ping Method**: `ping()` method implemented
- [ ] **Gateway Routes**: Gateway routes added
- [ ] **Docker Compose**: Service added to docker-compose.yml
- [ ] **Nginx Config**: Nginx configuration updated

### After Integration

- [ ] **Service Starts**: Service starts without errors
- [ ] **Health Check Works**: Health check endpoint responds
- [ ] **API Endpoints Work**: Gateway endpoints work correctly
- [ ] **Tests Pass**: All tests pass
- [ ] **Documentation Updated**: Documentation updated

---

## Section 4: API Endpoint Validation

### Before Creating Endpoint

- [ ] **Purpose Clear**: Endpoint purpose clearly defined
- [ ] **Auth Required**: Authentication requirements identified
- [ ] **Models Defined**: Request/response models designed
- [ ] **Error Cases Identified**: All error cases identified

### During Endpoint Creation

- [ ] **Router Created**: Router created with descriptive name
- [ ] **Auth Added**: Authentication dependency added if needed
- [ ] **Validation**: Request validation implemented
- [ ] **Error Handling**: Error handling implemented
- [ ] **Response Model**: Response model specified

### After Endpoint Creation

- [ ] **Endpoint Responds**: Endpoint responds correctly
- [ ] **Auth Works**: Authentication works as expected
- [ ] **Error Handling Works**: Error cases handled correctly
- [ ] **Tests Pass**: All tests pass
- [ ] **Docs Updated**: API documentation updated

---

## Section 5: Database Change Validation

### Before Database Changes

- [ ] **Backup Created**: Database backup created and verified ✅
- [ ] **Git Tag Created**: Git tag created ✅
- [ ] **Migration Reviewed**: Migration script reviewed by lead
- [ ] **Rollback Tested**: Rollback tested in staging ✅
- [ ] **Impact Assessed**: Impact on existing data assessed

### During Database Changes

- [ ] **Migration Script**: Migration script created
- [ ] **Models Updated**: SQLAlchemy models updated
- [ ] **Code Updated**: Application code updated if needed
- [ ] **Migration Tested**: Migration tested up and down

### After Database Changes

- [ ] **Migration Applied**: Migration applied successfully
- [ ] **App Works**: Application works with new schema
- [ ] **No Regressions**: No functionality regressions
- [ ] **Performance Acceptable**: Performance is acceptable

---

## Section 6: Test Validation

### Before Writing Tests

- [ ] **Strategy Defined**: Test strategy defined (unit/integration/e2e)
- [ ] **Test Cases Identified**: Test cases identified
- [ ] **Test Type Chosen**: Appropriate test type chosen

### During Test Writing

- [ ] **Tests Isolated**: Tests are isolated (no side effects)
- [ ] **External Services Mocked**: External services mocked
- [ ] **Edge Cases Covered**: Edge cases covered
- [ ] **Test Names Descriptive**: Test names clearly describe what they test

### After Writing Tests

- [ ] **All Tests Pass**: All tests pass
- [ ] **No Regressions**: No existing tests broken
- [ ] **Coverage Adequate**: Test coverage adequate (≥80% for new code)
- [ ] **Tests Fast**: Tests run quickly (< 1 minute for unit tests)

---

## Section 7: Documentation Validation

### Before Updating Documentation

- [ ] **Unique Info Identified**: Unique information identified
- [ ] **Cross-References Found**: All cross-references found
- [ ] **Preservation Record**: Preservation record created (if archiving)

### During Documentation Update

- [ ] **Content Accurate**: Content is accurate and up-to-date
- [ ] **Format Consistent**: Format follows documentation standards
- [ ] **Examples Work**: All code examples work
- [ ] **Links Valid**: All links are valid

### After Documentation Update

- [ ] **Cross-References Updated**: All cross-references updated
- [ ] **No Broken Links**: No broken links
- [ ] **Spell Checked**: Documentation spell-checked
- [ ] **Reviewed**: Documentation reviewed

---

## Section 8: Deployment Validation

### Before Deployment

- [ ] **Risk Assessed**: Risk level assessed
- [ ] **Backups**: Backups created (if required)
- [ ] **Git Tag**: Git tag created (if required)
- [ ] **Rollback Plan**: Rollback plan documented and tested
- [ ] **Staging Tested**: Changes tested in staging
- [ ] **Approvals**: Required approvals obtained

### During Deployment

- [ ] **Health Checks Pass**: Health checks pass
- [ ] **No Errors in Logs**: No errors in application logs
- [ ] **Metrics Normal**: Monitoring metrics are normal

### After Deployment

- [ ] **Functionality Verified**: Functionality verified
- [ ] **No Regressions**: No regressions detected
- [ ] **Performance Acceptable**: Performance is acceptable
- [ ] **Monitoring Active**: Monitoring is active and alerting

---

## Section 9: Risk-Level Specific Checklists

### LOW Risk Checklist

- [ ] Git commit created
- [ ] Single reviewer approval
- [ ] Tests pass
- [ ] Code formatted and linted

### MEDIUM Risk Checklist

Includes LOW risk items, plus:

- [ ] Git tag created ✅
- [ ] Backup created (if database changes)
- [ ] Two reviewers approved
- [ ] Rollback plan documented

### HIGH Risk Checklist

Includes MEDIUM risk items, plus:

- [ ] Full system backup created ✅
- [ ] Lead developer approval obtained ✅
- [ ] Staging tested ✅
- [ ] Rollback tested ✅
- [ ] On-call engineer notified

### CRITICAL Risk Checklist

Includes HIGH risk items, plus:

- [ ] Multiple backups created ✅
- [ ] Team consensus obtained ✅
- [ ] Staging fully tested ✅
- [ ] Rollback procedure tested ✅
- [ ] On-call engineer ready ✅
- [ ] Incident response plan ready

---

## Section 10: Quick Reference Table

| Task Type | Before | During | After |
|-----------|--------|--------|-------|
| **CONFIG** | Review existing config, plan changes | Follow config pattern, validate | Test config, verify app works |
| **CODE** | Identify pattern, plan types/errors | Follow pattern, add types/docs | Format, lint, test, document |
| **DOCS** | Identify unique info, find cross-refs | Write accurate content, check links | Update cross-refs, verify links |
| **TEST** | Define strategy, identify cases | Write isolated tests, mock services | Run tests, check coverage |
| **DEPLOY** | Assess risk, create backups, get approvals | Monitor health, check logs | Verify functionality, monitor |

---

## Section 11: Emergency Stop Conditions

### When to Stop Immediately

Stop execution immediately if:

- [ ] **Data Loss Risk**: Any operation that could cause data loss
- [ ] **Service Outage**: Operation would cause service outage
- [ ] **Security Breach**: Operation could create security vulnerability
- [ ] **Validation Failure**: Critical validation step fails
- [ ] **Unexpected Error**: Unexpected error occurs during execution
- [ ] **Approval Revoked**: Required approval is revoked

### What to Do When Stopping

1. **Stop Execution**: Immediately stop current operation
2. **Assess Situation**: Determine current state and impact
3. **Rollback if Needed**: Execute rollback plan if changes were made
4. **Document Incident**: Document what happened and why execution stopped
5. **Notify Team**: Notify appropriate team members
6. **Review**: Review what went wrong and update process

### Incident Reporting

When stopping due to emergency:

- [ ] Incident documented with:
  - What was being done
  - What went wrong
  - Current state
  - Actions taken
  - Next steps
- [ ] Team notified
- [ ] Incident reviewed to prevent recurrence

---

## See Also

- [AI_TASK_TEMPLATES.md](AI_TASK_TEMPLATES.md) - Task decomposition with validation requirements
- [AI_PRINCIPLES.md](AI_PRINCIPLES.md) - Core principles including risk-tiered operations
- [AI_PROMPT_LIBRARY.md](AI_PROMPT_LIBRARY.md) - Validation prompt templates
- [AI_PATTERNS.md](AI_PATTERNS.md) - Code patterns to validate against

---

**Last Updated**: 2024-01-01  
**Maintained By**: Project Team  
**Review Cycle**: Quarterly
