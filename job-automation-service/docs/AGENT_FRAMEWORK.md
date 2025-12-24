# Multi-Agent Testing and Gap Analysis Framework

## Overview

The Multi-Agent Testing and Gap Analysis Framework provides parallel execution of testing and analysis agents for the job automation service. It follows AI principles for deterministic coordination, scope-before-scale execution, and capability-based expansion.

## Architecture

The framework consists of:

1. **Agent Coordinator**: Manages task queue, dependency resolution, and parallel execution
2. **Lock Manager**: Database-based locking using PostgreSQL advisory locks
3. **Testing Agents**: Test scrapers, matchers, APIs, cover letters, and schedulers
4. **Gap Analysis Agents**: Analyze gaps, performance, security, documentation, and compliance
5. **Report Generator**: Aggregates results into Markdown and JSON reports

## Agent Types

### Testing Agents

- **scraper_test**: Tests job scrapers (Indeed, LinkedIn, Glassdoor, ZipRecruiter)
- **matcher_test**: Tests skills matching algorithm
- **api_test**: Tests all API endpoints
- **cover_letter_test**: Tests cover letter generation
- **scheduler_test**: Tests scheduled job searches

### Gap Analysis Agents

- **gap_analysis**: Identifies missing/incomplete features
- **performance_analysis**: Analyzes performance bottlenecks
- **security_analysis**: Identifies security issues
- **doc_analysis**: Checks documentation completeness
- **compliance_analysis**: Validates ToS and compliance

## Task Definition Guide

### Basic Task Definition

```python
{
    "id": "unique-task-id",
    "agent_type": AgentType.API_TEST,
    "description": "Test API endpoints",
    "dependencies": [],  # List of task IDs this depends on
    "priority": 5,  # Higher = more important
    "timeout": 300  # Optional, seconds
}
```

### Task Dependencies

Tasks can depend on other tasks. The coordinator ensures dependencies are completed before starting a task:

```python
{
    "id": "test-cover-letter",
    "agent_type": AgentType.COVER_LETTER_TEST,
    "dependencies": ["test-matcher"],  # Waits for matcher test
    "priority": 4
}
```

### Task Priority

Higher priority tasks are scheduled first when multiple tasks are available:
- **5**: Critical tests
- **4**: Important tests
- **3**: Analysis tasks
- **2**: Documentation tasks
- **1**: Low priority

## Coordination Mechanisms

### Database Advisory Locks

The framework uses PostgreSQL advisory locks for atomic task coordination:

- Lock key generated from task ID hash
- Automatic expiration prevents deadlocks
- Lock token for validation
- File-based fallback if database unavailable

### Task Status States

- **pending**: Task is queued
- **in_progress**: Task is running
- **completed**: Task finished successfully
- **failed**: Task encountered an error
- **blocked**: Task dependencies not met

### Dependency Resolution

The coordinator:
1. Builds dependency graph from task definitions
2. Performs topological sort for execution order
3. Executes independent tasks in parallel
4. Detects blocked tasks (circular dependencies or missing dependencies)

## Usage

### Basic Usage

```bash
# Run full test suite
python -m tests.agents.run_agents

# Or use PowerShell
.\tests\agents\run_agents.ps1

# Or use Bash
./tests/agents/run_agents.sh
```

### Command Line Options

```bash
# Run specific agents
python -m tests.agents.run_agents --agents api_test matcher_test

# Use predefined suite
python -m tests.agents.run_agents --suite quick

# Set max parallel agents
python -m tests.agents.run_agents --max-parallel 5

# Specify output directory
python -m tests.agents.run_agents --output /path/to/reports

# Enable verbose logging
python -m tests.agents.run_agents --verbose
```

### Predefined Suites

- **quick**: Minimal test suite (API + Matcher)
- **full**: All agents (testing + analysis)
- **gap**: Gap analysis only
- **performance**: Performance testing suite
- **custom**: Custom agent selection

## Scaling Guidelines

Following "Scope Before Scale" principle:

### Phase 1: Single Agent Validation
- Test with 1 agent at a time
- Verify operations complete successfully
- Measure performance and resource usage
- Document edge cases

### Phase 2: Small Multi-Agent (2-3 agents)
- Test coordination mechanisms
- Verify no resource conflicts
- Measure coordination overhead
- Default: `max_parallel=3`

### Phase 3: Full Parallel Execution
- Run all independent tasks in parallel
- Monitor for degradation
- Validate coordination at scale

### Phase 4: Expand Capability
- Add new agent types (not more of the same type)
- Breadth before parallelism

## Creating Custom Agents

### 1. Define Agent Function

```python
async def my_custom_agent(task: AgentTask) -> Dict[str, Any]:
    """My custom agent implementation."""
    results = {
        "tests_run": 0,
        "success_count": 0,
        "errors": []
    }
    
    # Your agent logic here
    try:
        # Do work
        results["tests_run"] = 1
        results["success_count"] = 1
    except Exception as e:
        results["errors"].append(str(e))
    
    return results
```

### 2. Register Agent Type

Add to `AgentType` enum in `coordinator.py`:

```python
class AgentType(str, Enum):
    # ... existing types ...
    MY_CUSTOM_AGENT = "my_custom_agent"
```

### 3. Register Agent Function

In `run_agents.py`:

```python
coordinator.register_agent(AgentType.MY_CUSTOM_AGENT, my_custom_agent)
```

### 4. Create Task

```python
coordinator.add_task(
    task_id="my-custom-task",
    agent_type=AgentType.MY_CUSTOM_AGENT,
    description="My custom task",
    dependencies=[],
    priority=5
)
```

## Database Schema

### agent_tasks Table

Stores task definitions and execution status:

- `id`: Unique task identifier
- `agent_type`: Type of agent
- `description`: Task description
- `status`: Current status (pending, in_progress, completed, failed)
- `priority`: Task priority
- `dependencies`: JSON array of task IDs
- `assigned_agent`: Agent ID running the task
- `started_at`: Task start timestamp
- `completed_at`: Task completion timestamp
- `result`: JSON results from agent
- `error`: Error message if failed
- `timeout`: Task timeout in seconds

### agent_locks Table

Stores active locks for coordination:

- `task_id`: Foreign key to agent_tasks
- `agent_id`: Agent holding the lock
- `acquired_at`: Lock acquisition timestamp
- `expires_at`: Lock expiration timestamp
- `lock_token`: Unique lock token

## Reports

### Markdown Report

Generated at `tests/agents/reports/report_YYYYMMDD_HHMMSS.md`:

- Executive summary
- Test results by category
- Gap analysis findings
- Performance metrics
- Security findings
- Recommendations

### JSON Report

Generated at `tests/agents/reports/report_YYYYMMDD_HHMMSS.json`:

Structured data with:
- Metadata (timestamps, task counts)
- Test results array
- Analysis results array
- Summary statistics

## Troubleshooting

### Agents Not Starting

**Issue**: Tasks remain in "pending" status

**Solutions**:
1. Check dependencies are completed
2. Verify agent function is registered
3. Check database connection
4. Review coordinator logs

### Lock Timeout Errors

**Issue**: `TimeoutError: Could not acquire lock`

**Solutions**:
1. Check for stuck locks: `SELECT * FROM agent_locks WHERE expires_at < NOW()`
2. Clean expired locks manually
3. Increase lock timeout in config
4. Check database connectivity

### Database Connection Errors

**Issue**: Cannot connect to database

**Solutions**:
1. Verify `DATABASE_URL` environment variable
2. Check database is running
3. Verify credentials
4. Framework will fallback to file-based locking if enabled

### Agent Execution Failures

**Issue**: Tasks fail with errors

**Solutions**:
1. Check agent logs for specific errors
2. Verify service dependencies (API running, Ollama available, etc.)
3. Review task timeout settings
4. Check agent function implementation

### Circular Dependencies

**Issue**: Tasks blocked indefinitely

**Solutions**:
1. Review task dependency graph
2. Remove circular dependencies
3. Tasks will be marked as "blocked" after timeout

## Best Practices

1. **Start Small**: Begin with single agent, then scale
2. **Use Dependencies**: Properly define task dependencies
3. **Set Priorities**: Use priority to control execution order
4. **Handle Errors**: Agents should catch and report errors gracefully
5. **Monitor Resources**: Watch database connections and system resources
6. **Review Reports**: Regularly review generated reports for insights

## Configuration

Edit `tests/agents/config.py` to customize:

- `max_parallel_agents`: Default parallel execution limit (default: 3)
- `default_task_timeout`: Default task timeout in seconds (default: 300)
- `lock_timeout`: Lock acquisition timeout (default: 60)
- `lock_expiration`: Lock expiration time (default: 600)
- `report_output_dir`: Report output directory
- `enable_file_lock_fallback`: Enable file-based lock fallback

## Integration with CI/CD

The framework can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Agent Tests
  run: |
    cd job-automation-service
    python -m tests.agents.run_agents --suite quick
    
- name: Upload Reports
  uses: actions/upload-artifact@v3
  with:
    name: agent-reports
    path: job-automation-service/tests/agents/reports/
```

## Related Documentation

- [AI Principles](../docs/AI_PRINCIPLES.md) - Core principles for multi-agent coordination
- [AI Task Templates](../docs/AI_TASK_TEMPLATES.md) - Task decomposition templates
- [Job Automation Service README](../README.md) - Service documentation

