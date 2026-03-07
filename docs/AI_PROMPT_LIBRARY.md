# AI Prompt Library - Reusable Prompt Templates

**Purpose**: Standardized prompt templates for common AI agent operations to promote consistent, safe, and effective interactions.

**How to Use Prompts**: 
- Select the prompt template that matches your task
- Replace placeholders (e.g., `{task_description}`) with actual values
- Customize as needed for specific scenarios
- Use in combination with other prompts when appropriate

**Customization Guidelines**: 
- Replace all placeholders with actual values
- Add task-specific requirements
- Include relevant context from codebase
- Reference related documents when applicable

**Related Documents**:
- [AI_TASK_TEMPLATES.md](AI_TASK_TEMPLATES.md) - Task decomposition templates
- [AI_VALIDATION_CHECKLIST.md](AI_VALIDATION_CHECKLIST.md) - Validation requirements
- [AI_PATTERNS.md](AI_PATTERNS.md) - Code patterns to follow
- [AI_PRINCIPLES.md](AI_PRINCIPLES.md) - Core principles

---

## Prompt 1: Task Decomposition Prompt

**When to Use**: When starting a new task that needs to be broken down into subtasks.

**Template**:

```
Decompose the following task into subtasks:

Task: {task_description}

Requirements:
1. Identify all subtasks required to complete this task
2. Map dependencies between subtasks (which tasks depend on which)
3. Identify parallelization opportunities (which tasks can run in parallel)
4. Estimate risk level for each subtask (LOW, MEDIUM, HIGH, CRITICAL)
5. Estimate time for each subtask
6. Identify file locations for each subtask (use AI_CODEBASE_MAP.md for reference)

Output Format:
- List of subtasks with:
  - Task number and description
  - Dependencies (list of task numbers)
  - Risk level
  - Estimated time
  - File locations
- Dependency graph (text or mermaid format)
- Parallelization opportunities
- Rollback plan outline

Reference Documents:
- AI_TASK_TEMPLATES.md for similar task templates
- AI_CODEBASE_MAP.md for file locations
- AI_PRINCIPLES.md for risk assessment guidelines
```

**Expected Output Format**:
- Numbered list of subtasks
- Dependency graph
- Parallelization opportunities
- Risk levels
- File locations

**Integration**: Use with [AI_TASK_TEMPLATES.md](AI_TASK_TEMPLATES.md) to find similar templates.

---

## Prompt 2: Code Review Prompt

**When to Use**: When reviewing code changes before approval.

**Template**:

```
Review the following code changes for approval:

Code Changes: {code_diff_or_description}
Risk Level: {risk_level}
Task Type: {task_type}

Review Criteria:
1. Code follows patterns from AI_PATTERNS.md
2. Type hints present on all functions
3. Docstrings present on all public functions
4. Error handling implemented appropriately
5. Tests written and passing
6. No hardcoded values
7. Configuration follows patterns
8. Documentation updated if needed

Risk Assessment:
- Does the risk level match the changes?
- Are appropriate safeguards in place?
- Is rollback plan adequate?

Approval Decision:
- [ ] APPROVE - Code is ready
- [ ] REQUEST CHANGES - Issues found (list below)
- [ ] REJECT - Critical issues (list below)

Issues Found:
{list_of_issues}

Reference Documents:
- AI_PATTERNS.md for code patterns
- AI_VALIDATION_CHECKLIST.md for validation requirements
- AI_PRINCIPLES.md for risk assessment
```

**Review Criteria Checklist**:
- Pattern compliance
- Type hints
- Docstrings
- Error handling
- Tests
- Configuration
- Documentation

**Approval/Rejection Format**: Clear decision with justification.

---

## Prompt 3: Service Integration Prompt

**When to Use**: When integrating a new external service.

**Template**:

```
Integrate the following service into the platform:

Service: {service_name}
Service Type: {service_type}
API Documentation: {api_docs_url}

Pre-requisite Checks:
1. Review service API documentation
2. Identify health check endpoint
3. Identify authentication method
4. Document required environment variables
5. Verify Docker image availability
6. Understand network requirements

Step-by-Step Guidance:
1. Create service configuration class following pattern from services/{existing_service}/config.py
2. Create service client class following pattern from services/{existing_service}/{service}_client.py
3. Implement async context manager (__aenter__, __aexit__)
4. Implement ping() method for health checks
5. Implement core API methods
6. Add gateway routes in app/api/gateway.py
7. Update docker-compose.yml
8. Update nginx/nginx.conf
9. Write unit tests in tests/unit/test_{service}_client.py
10. Write integration tests in tests/integration/test_{service}_gateway.py
11. Update documentation

Validation Requirements:
- Complete checklist from AI_VALIDATION_CHECKLIST.md Section 3
- Follow patterns from AI_PATTERNS.md Section 1
- Use file locations from AI_CODEBASE_MAP.md Section 3

Reference Documents:
- AI_PATTERNS.md Section 1 for service client pattern
- AI_TASK_TEMPLATES.md Template 1 for task breakdown
- AI_CODEBASE_MAP.md Section 3 for file locations
```

**Pre-requisite Checks**: API review, health endpoint, auth method, env vars, Docker image.

**Integration with AI_PATTERNS.md**: Follows service client pattern from Section 1.

---

## Prompt 4: Bug Fix Prompt

**When to Use**: When fixing a bug in the codebase.

**Template**:

```
Fix the following bug:

Bug Description: {bug_description}
Steps to Reproduce: {steps_to_reproduce}
Expected Behavior: {expected_behavior}
Actual Behavior: {actual_behavior}
Affected Files: {affected_files}

Test-First Approach:
1. Write a failing test that reproduces the bug
2. Implement the fix
3. Verify the test passes
4. Add regression tests to prevent recurrence

Root Cause Focus:
- Identify the root cause, not just symptoms
- Fix the underlying issue
- Ensure fix doesn't introduce new issues

Regression Prevention:
- Add tests for the bug scenario
- Add tests for related edge cases
- Verify no other functionality is affected

Validation:
- Complete checklist from AI_VALIDATION_CHECKLIST.md Section 2
- Follow patterns from AI_PATTERNS.md
- Use template from AI_TASK_TEMPLATES.md Template 4

Reference Documents:
- AI_TASK_TEMPLATES.md Template 4 for bug fix template
- AI_PATTERNS.md for code patterns
- AI_VALIDATION_CHECKLIST.md Section 2 for validation
```

**Test-First Approach**: Write failing test, fix, verify.

**Root Cause Focus**: Fix underlying issue, not symptoms.

---

## Prompt 5: Refactoring Prompt

**When to Use**: When refactoring existing code.

**Template**:

```
Refactor the following code:

Code to Refactor: {code_location_or_description}
Refactoring Goal: {refactoring_goal}
Target Pattern: {target_pattern_from_AI_PATTERNS.md}

Safety Requirements:
1. Ensure test coverage is adequate (≥80%) before refactoring
2. Create git tag before starting: git tag -a pre-refactor-{name}-{timestamp}
3. Refactor incrementally (small, testable changes)
4. Run tests after each change
5. Commit working state frequently

Incremental Approach:
- Make one small change at a time
- Test after each change
- Only proceed if tests pass
- Document learnings

Test Coverage Emphasis:
- Verify existing tests cover functionality
- Add tests if coverage insufficient
- Update tests to match new structure
- Ensure all tests pass

Validation:
- Complete checklist from AI_VALIDATION_CHECKLIST.md Section 2
- Follow patterns from AI_PATTERNS.md
- Use template from AI_TASK_TEMPLATES.md Template 6

Reference Documents:
- AI_TASK_TEMPLATES.md Template 6 for refactoring template
- AI_PATTERNS.md for target patterns
- AI_PRINCIPLES.md Section 5 for iteration principles
```

**Safety Requirements**: Test coverage, git tag, incremental changes.

**Incremental Approach**: Small, testable changes with frequent commits.

---

## Prompt 6: Documentation Update Prompt

**When to Use**: When updating documentation.

**Template**:

```
Update the following documentation:

Document: {document_path}
Update Type: {new_content|update_existing|archive}
Content Changes: {description_of_changes}

Preservation Process (if archiving):
1. Extract unique information from document
2. Create preservation record with:
   - Source location
   - Destination location
   - Unique information extracted
   - Cross-references
   - Preservation date
3. Update archive index
4. Update all cross-references

Integrity Verification:
1. Verify all links work
2. Verify cross-references are updated
3. Spell check document
4. Verify examples work (if code examples)

Cross-Reference Updates:
1. Find all references to updated document
2. Update links and references
3. Verify no broken links

Validation:
- Complete checklist from AI_VALIDATION_CHECKLIST.md Section 7
- Follow preservation process from AI_PRINCIPLES.md Section 3
- Use template from AI_TASK_TEMPLATES.md Template 5

Reference Documents:
- AI_PRINCIPLES.md Section 3 for preservation process
- AI_TASK_TEMPLATES.md Template 5 for documentation template
- AI_VALIDATION_CHECKLIST.md Section 7 for validation
```

**Preservation Process**: Extract unique info, create preservation record, update cross-refs.

**Integrity Verification**: Links, cross-refs, spelling, examples.

---

## Prompt 7: Database Migration Prompt

**When to Use**: When creating or applying database migrations.

**Template**:

```
Create/Apply database migration:

Migration Type: {create_new|apply_existing}
Migration Description: {description}
Risk Level: CRITICAL

CRITICAL Risk Emphasis:
- Database migrations are CRITICAL risk operations
- Require full backups, lead approval, staging testing
- Rollback must be tested before applying

Pre-Approval Requirements:
1. Create database backup: ./scripts/automation/backup.sh --type=database --tag=pre-migration-{name}
2. Verify backup integrity
3. Create git tag: git tag -a pre-migration-{name}-{timestamp}
4. Get lead developer approval
5. Test in staging environment

Staging Validation:
1. Apply migration in staging: alembic upgrade head
2. Verify schema changes
3. Test application functionality
4. Test rollback: alembic downgrade -1
5. Re-apply migration: alembic upgrade head

Rollback Testing:
- Test rollback procedure in staging
- Verify data integrity after rollback
- Document rollback steps

Validation:
- Complete checklist from AI_VALIDATION_CHECKLIST.md Section 5
- Follow template from AI_TASK_TEMPLATES.md Template 3
- Ensure all CRITICAL risk requirements met

Reference Documents:
- AI_TASK_TEMPLATES.md Template 3 for migration template
- AI_VALIDATION_CHECKLIST.md Section 5 for validation
- AI_PRINCIPLES.md Section 1 for risk-tiered operations
```

**CRITICAL Risk Emphasis**: Full backups, lead approval, staging testing required.

**Pre-Approval Requirements**: Backup, git tag, lead approval, staging test.

---

## Prompt 8: Pre-Execution Validation Prompt

**When to Use**: Before executing any task to ensure safety.

**Template**:

```
Validate the following task before execution:

Task: {task_description}
Task Type: {task_type}
Risk Level: {risk_level}

Universal Validation Checklist:
1. Task decomposed into subtasks
2. Dependencies identified
3. Risk level assigned and justified
4. Rollback plan documented
5. Human approval obtained (if required)
6. Backups created (if required)
7. Git tag created (if required)
8. Dependencies verified

Risk Level Confirmation:
- LOW: Git commit, single reviewer, tests pass
- MEDIUM: + Git tag, backup, two reviewers, rollback plan
- HIGH: + Full backup, lead approval, staging tested, rollback tested
- CRITICAL: + Multiple backups, team consensus, on-call ready

Safety Check Emphasis:
- No execution until all validation items complete
- Stop immediately if any critical validation fails
- Document any validation issues

Validation Status:
- [ ] All validation items complete
- [ ] Ready for execution
- [ ] Issues found (list below)

Issues Found:
{list_of_issues}

Reference Documents:
- AI_VALIDATION_CHECKLIST.md for complete checklist
- AI_PRINCIPLES.md Section 1 for risk-tiered operations
```

**Universal Validation Checklist**: Task decomposition, dependencies, risk, rollback, approval, backups.

**Risk Level Confirmation**: Verify appropriate safeguards for risk level.

---

## Prompt 9: Code Generation Prompt

**When to Use**: When generating new code.

**Template**:

```
RETRIEVE BEFORE GENERATE (required):
1. Consult docs/coding_standards_matrix.md for relevant domain standards
2. Identify applicable patterns and reference implementations (internal + external)
3. Read AI_PATTERNS.md Section(s) for the pattern(s) you will use
4. Locate similar code in codebase via AI_CODEBASE_MAP.md
5. Summarize: Standards applied | Reference code used | Design plan
6. Only then proceed to implementation

Output sections (in order):
- Standards applied (from matrix)
- Reference code used (internal paths + external links if consulted)
- Design plan (brief)
- Implementation

---

Generate code for the following:

Feature: {feature_description}
Location: {file_path}
Pattern: {pattern_from_AI_PATTERNS.md}

Pattern Reference Requirement:
- Follow pattern from AI_PATTERNS.md Section {section_number}
- Reference existing code: {similar_code_location}
- Maintain consistency with codebase

Code Quality Requirements:
1. Type hints on all functions
2. Docstrings on all public functions
3. Error handling implemented
4. No hardcoded values (use configuration)
5. Follow naming conventions
6. Follow import organization

Testing Requirements:
1. Write unit tests
2. Write integration tests (if applicable)
3. Ensure tests pass
4. Achieve adequate coverage (≥80%)

Documentation Requirements:
1. Update API documentation (if API endpoint)
2. Update code comments
3. Update relevant documentation files

Validation:
- Complete checklist from AI_VALIDATION_CHECKLIST.md Section 2
- Follow patterns from AI_PATTERNS.md
- Use file locations from AI_CODEBASE_MAP.md

Reference Documents:
- docs/coding_standards_matrix.md for standards and reference implementations
- AI_PATTERNS.md for code patterns
- AI_CODEBASE_MAP.md for file locations
- AI_VALIDATION_CHECKLIST.md Section 2 for validation

CRITIC (before finalizing):
Produce model-as-judge critic report (domain: code). Check: Did you cite standards and references before implementation?
{
  "pass": true|false,
  "score": 0.0-1.0,
  "issues": [{"type": "...", "detail": "..."}],
  "fixes": [{"action": "...", "detail": "..."}]
}
If pass=false or score below threshold, revise output. Include final critic report in response summary.
```

**Pattern Reference Requirement**: Must follow patterns from AI_PATTERNS.md.

**Code Quality Requirements**: Type hints, docstrings, error handling, configuration, naming.

---

## Prompt 10: Testing Prompt

**When to Use**: When writing tests.

**Template**:

```
Write tests for the following:

Code to Test: {code_location_or_description}
Test Type: {unit|integration|e2e}

Test Type Selection:
- Unit: Test individual functions/classes in isolation
- Integration: Test components working together (with database)
- E2E: Test complete user workflows

Test Pattern Reference:
- Unit tests: tests/unit/test_{feature}.py
- Integration tests: tests/integration/test_{feature}.py
- E2E tests: tests/e2e/test_{workflow}.py
- Follow patterns from AI_PATTERNS.md Section 4

Coverage Requirements:
- Unit tests: ≥80% coverage for new code
- Integration tests: Cover main workflows
- E2E tests: Cover critical user paths

Isolation Requirements:
- Tests are isolated (no side effects)
- External services mocked (use respx)
- Test data cleaned up
- Use fixtures from tests/conftest.py

Validation:
- Complete checklist from AI_VALIDATION_CHECKLIST.md Section 6
- Follow patterns from AI_PATTERNS.md Section 4

Reference Documents:
- AI_PATTERNS.md Section 4 for test patterns
- AI_VALIDATION_CHECKLIST.md Section 6 for validation
- AI_CODEBASE_MAP.md Section 5 for test structure
```

**Test Type Selection**: Choose appropriate test type (unit/integration/e2e).

**Test Pattern Reference**: Follow patterns from AI_PATTERNS.md Section 4.

---

## Prompt 11: Error Handling Prompt

**When to Use**: When implementing error handling.

**Template**:

```
Implement error handling for the following:

Code Location: {code_location}
Operation: {operation_description}

Exception Identification:
- Identify all possible exceptions
- Categorize by type (network, validation, business logic)
- Determine appropriate handling for each

Handling Strategy:
- Use HTTPException for API endpoints (with appropriate status codes)
- Use logging for errors (logger.error with exc_info=True)
- Return None or empty collections for service clients
- Raise exceptions for critical errors

Logging Requirements:
- Log errors with context
- Use appropriate log levels (error, warning, info)
- Include exception information (exc_info=True)
- Don't log sensitive information

User-Facing Messages:
- Provide clear, user-friendly error messages
- Don't expose technical details to users
- Include actionable guidance when possible

Validation:
- Follow patterns from AI_PATTERNS.md Section 5
- Ensure all error cases handled

Reference Documents:
- AI_PATTERNS.md Section 5 for error handling patterns
- AI_PRINCIPLES.md for error handling principles
```

**Exception Identification**: Identify all possible exceptions.

**Handling Strategy**: HTTPException, logging, return values, raise exceptions.

---

## Prompt 12: Configuration Prompt

**When to Use**: When adding or modifying configuration.

**Template**:

```
Add/Update configuration for the following:

Configuration Type: {application|service|deployment}
Configuration Name: {config_name}

Location Decision:
- Application config: app/config.py
- Service config: services/{service_name}/config.py
- Deployment config: docker-compose.yml, .env.example

Pydantic Pattern:
- Extend pydantic_settings.BaseSettings
- Use env_prefix for environment variables
- Provide sensible defaults
- Add validation if needed

Environment Variable Naming:
- Use UPPER_SNAKE_CASE
- Prefix service-specific vars: {SERVICE}_BASE_URL
- Use descriptive names

Documentation Requirements:
- Document all configuration options
- Update .env.example
- Document default values
- Document environment variable names

Validation:
- Follow patterns from AI_PATTERNS.md Section 6
- Use file locations from AI_CODEBASE_MAP.md

Reference Documents:
- AI_PATTERNS.md Section 6 for configuration patterns
- AI_CODEBASE_MAP.md for file locations
```

**Location Decision**: Choose appropriate location (app/config.py, services/{service}/config.py, etc.).

**Pydantic Pattern**: Extend BaseSettings, use env_prefix, provide defaults.

---

## Prompt 13: Deployment Prompt

**When to Use**: When deploying changes.

**Template**:

```
Deploy the following changes:

Changes: {description_of_changes}
Risk Level: {risk_level}
Environment: {staging|production}

Risk-Level Specific Requirements:
- LOW: Git commit, single reviewer, tests pass
- MEDIUM: + Git tag, backup, two reviewers, rollback plan
- HIGH: + Full backup, lead approval, staging tested, rollback tested
- CRITICAL: + Multiple backups, team consensus, on-call ready

Pre-Deployment Checklist:
1. Complete validation from AI_VALIDATION_CHECKLIST.md Section 8
2. Create backups (if required)
3. Create git tag (if required)
4. Get approvals (if required)
5. Test in staging (if required)
6. Verify rollback plan

During Deployment Monitoring:
1. Monitor health checks
2. Check application logs for errors
3. Monitor metrics for anomalies
4. Be ready to rollback if issues

Post-Deployment Verification:
1. Verify functionality works
2. Check for regressions
3. Verify performance acceptable
4. Ensure monitoring active

Validation:
- Complete checklist from AI_VALIDATION_CHECKLIST.md Section 8
- Follow risk-level requirements from AI_PRINCIPLES.md Section 1

Reference Documents:
- AI_VALIDATION_CHECKLIST.md Section 8 for deployment validation
- AI_PRINCIPLES.md Section 1 for risk-tiered operations
```

**Risk-Level Specific Requirements**: Different requirements for LOW/MEDIUM/HIGH/CRITICAL.

**Pre-Deployment Checklist**: Validation, backups, approvals, staging test.

---

## Prompt 14: Emergency Rollback Prompt

**When to Use**: When rolling back changes due to issues.

**Template**:

```
Execute emergency rollback for the following:

Change: {description_of_change}
Issue: {description_of_issue}
Risk Level: {risk_level}

Situation Assessment:
1. Assess current state
2. Determine rollback scope
3. Identify rollback method (git revert, migration downgrade, etc.)
4. Verify rollback plan is available

Rollback Execution:
1. Stop current operation if in progress
2. Execute rollback steps:
   - Git rollback: git revert <commit> or git reset --hard <tag>
   - Database rollback: alembic downgrade -1 or restore backup
   - Service rollback: docker-compose down && docker-compose up -d
3. Verify rollback successful

Verification Steps:
1. Verify application works after rollback
2. Verify no data loss
3. Verify functionality restored
4. Monitor for stability

Documentation Requirements:
1. Document what was rolled back
2. Document why rollback was needed
3. Document rollback steps taken
4. Document lessons learned

Reference Documents:
- AI_TASK_TEMPLATES.md for rollback plans
- AI_PRINCIPLES.md Section 1 for reversibility principles
```

**Situation Assessment**: Assess state, determine scope, identify method.

**Rollback Execution**: Stop operation, execute rollback, verify.

---

## Prompt 15: Pattern Extraction Prompt

**When to Use**: When internalizing a new repository into reusable engineering pattern docs.

**Template**:

```
Analyze the following repository and extract a reusable engineering pattern document.

Repository: {repo_path_or_url}
Target output: Add to docs/ or update AI_PATTERNS.md

Extract:
1. Directory structure
2. Architecture pattern (e.g., layered, modular, gateway)
3. Dependency management (requirements.txt, pyproject.toml)
4. Testing approach (framework, fixtures, mocking)
5. Security patterns (auth, validation, rate limiting)
6. API conventions (REST, OpenAPI, error codes)

Output format:
- pattern: {short_name}
- structure: {directory tree}
- principles: [list]
- benefits: [list]
- reference_files: [paths or URLs]
- checklist: [items for new implementations]

Convert output into a markdown document suitable for AI_PATTERNS.md or a new docs/coding_standards_matrix.md row.
```

**Integration**: Use when onboarding a new reference repo. Output can feed into AI_PATTERNS.md or coding_standards_matrix.md Table 2.

---

## Prompt 16: Code Quality Auditor Prompt

**When to Use**: When reviewing code against canonical standards and patterns.

**Template**:

```
Act as a software architecture reviewer.

Compare the current code against:
- docs/coding_standards_matrix.md Table 1 (PEP8, OpenAPI, OWASP, SQLAlchemy, etc.)
- AI_PATTERNS.md patterns

Return:
1. Violations (with standard/pattern reference)
2. Security risks (OWASP mapping)
3. Architectural smells
4. Suggested refactor
```

**Integration**: Complements Code Review prompt (Prompt 2) with explicit standards-matrix alignment.

---

## Prompt 17: Matrix Generation Prompt

**When to Use**: When onboarding new reference repositories to extend the coding standards matrix.

**Template**:

```
Scan the following repositories and extract coding standards:

Repositories: {repo_paths_or_urls}

Extract:
- formatting rules
- architecture patterns
- testing practices
- security patterns

Produce a matrix linking: pattern | repository | documentation | example file

Output markdown table suitable for docs/coding_standards_matrix.md Table 2.
```

**Integration**: Use with Pattern Extraction (Prompt 15) when adding new reference repos. Output feeds into coding_standards_matrix.md.

---

## Section: Prompt Usage Guidelines

### When to Use Each Prompt

| Prompt | When to Use |
|--------|-------------|
| **Task Decomposition** | Starting new task |
| **Code Review** | Reviewing code changes |
| **Service Integration** | Integrating new service |
| **Bug Fix** | Fixing bugs |
| **Refactoring** | Refactoring code |
| **Documentation Update** | Updating documentation |
| **Database Migration** | Creating/applying migrations |
| **Pre-Execution Validation** | Before any task execution |
| **Code Generation** | Generating new code |
| **Testing** | Writing tests |
| **Error Handling** | Implementing error handling |
| **Configuration** | Adding/updating configuration |
| **Deployment** | Deploying changes |
| **Emergency Rollback** | Rolling back changes |
| **Pattern Extraction** | Internalizing new repo into pattern docs |
| **Code Quality Auditor** | Reviewing code against standards matrix |
| **Matrix Generation** | Extending matrix from new reference repos |

### How to Customize Prompts

1. **Replace Placeholders**: Replace all `{placeholder}` values with actual values
2. **Add Context**: Include relevant codebase context
3. **Specify Requirements**: Add task-specific requirements
4. **Reference Documents**: Include specific document sections when relevant

### Best Practices

1. **Be Specific**: Provide specific file paths, code locations, and requirements
2. **Include Context**: Include relevant codebase context
3. **Reference Documents**: Always reference relevant AI documentation
4. **Validate**: Complete validation checklists before execution

### Prompt Combination Strategies

- **Task Decomposition + Pre-Execution Validation**: Decompose task, then validate
- **Code Generation + Testing**: Generate code, then write tests
- **Service Integration + Deployment**: Integrate service, then deploy
- **Bug Fix + Code Review**: Fix bug, then review
- **Pattern Extraction + Code Generation**: Extract pattern from new repo, then use for future code
- **Code Generation + Code Quality Auditor**: Generate code, then audit against standards
- **Matrix Generation + Pattern Extraction**: Scan repos for matrix, then extract full pattern docs

---

## Section: Prompt Customization Examples

### Example 1: Customizing Task Decomposition Prompt

**Original**:
```
Decompose the following task: {task_description}
```

**Customized**:
```
Decompose the following task: Add Nextcloud service integration

Specific Requirements:
- Nextcloud API v2.0
- OAuth2 authentication
- File sync functionality
- Health check endpoint: /status.php

Reference existing service: services/file_storage/seafile_client.py
```

### Example 2: Customizing Code Generation Prompt

**Original**:
```
Generate code for: {feature_description}
```

**Customized**:
```
Generate code for: User profile endpoint

Requirements:
- GET /api/users/{user_id}/profile
- Requires authentication
- Returns user profile data
- Follow pattern from app/api/gateway.py

Reference: app/api/services.py for similar endpoint structure
```

### Placeholder Replacement Guide

| Placeholder | Example Replacement |
|-------------|---------------------|
| `{task_description}` | "Add Nextcloud service integration" |
| `{service_name}` | "nextcloud" |
| `{file_path}` | "app/api/users.py" |
| `{risk_level}` | "MEDIUM" |
| `{task_type}` | "CODE" |
| `{code_location}` | "app/api/gateway.py" |
| `{pattern_from_AI_PATTERNS.md}` | "Service Client Pattern (Section 1)" |

---

## See Also

- [AI_TASK_TEMPLATES.md](AI_TASK_TEMPLATES.md) - Task decomposition templates
- [AI_VALIDATION_CHECKLIST.md](AI_VALIDATION_CHECKLIST.md) - Validation requirements
- [AI_PATTERNS.md](AI_PATTERNS.md) - Code patterns to follow
- [AI_PRINCIPLES.md](AI_PRINCIPLES.md) - Core principles

---

**Last Updated**: 2024-01-01  
**Maintained By**: Project Team  
**Review Cycle**: Quarterly
