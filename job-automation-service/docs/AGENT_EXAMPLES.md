# Agent Framework Examples

This document provides examples and tutorials for using the multi-agent testing and gap analysis framework.

## Quick Start

### Running a Single Agent

```bash
cd job-automation-service
python -m tests.agents.run_agents --agents api_test
```

### Running Multiple Agents

```bash
python -m tests.agents.run_agents --agents api_test matcher_test gap_analysis
```

### Running a Predefined Suite

```bash
# Quick test suite
python -m tests.agents.run_agents --suite quick

# Full test suite
python -m tests.agents.run_agents --suite full

# Gap analysis only
python -m tests.agents.run_agents --suite gap
```

## Creating a Custom Agent

### Example: Custom Test Agent

```python
# tests/agents/custom_test_agent.py
import logging
from typing import Dict, Any
from app.models.agent_task import AgentTask

logger = logging.getLogger(__name__)

async def custom_test_agent(task: AgentTask) -> Dict[str, Any]:
    """Custom test agent example.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with test results
    """
    results = {
        "tests_run": 0,
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        # Your test logic here
        logger.info(f"Running custom test for task {task.id}")
        
        # Example: Test something
        test_result = perform_test()
        
        results["tests_run"] = 1
        if test_result:
            results["passed"] = 1
        else:
            results["failed"] = 1
            results["errors"].append("Test failed")
            
    except Exception as e:
        logger.error(f"Custom test failed: {e}")
        results["failed"] = 1
        results["errors"].append(str(e))
    
    return results
```

### Registering Your Agent

```python
# In tests/agents/run_agents.py
from tests.agents.custom_test_agent import custom_test_agent

# Add to AgentType enum
class AgentType(str, Enum):
    # ... existing types ...
    CUSTOM_TEST = "custom_test"

# Register agent
coordinator.register_agent(AgentType.CUSTOM_TEST, custom_test_agent)
```

## Best Practices

### 1. Error Handling

Always include comprehensive error handling:

```python
async def my_agent(task: AgentTask) -> Dict[str, Any]:
    results = {"errors": []}
    
    try:
        # Your logic
        pass
    except SpecificError as e:
        logger.error(f"Specific error: {e}")
        results["errors"].append({"type": "specific", "message": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        results["errors"].append({"type": "unexpected", "message": str(e)})
    
    return results
```

### 2. Retry Logic

Implement retry logic for transient failures:

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        result = await perform_operation()
        break  # Success
    except TransientError as e:
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        else:
            raise
```

### 3. Logging

Use structured logging:

```python
logger.info(f"Starting agent {task.id}")
logger.debug(f"Processing with parameters: {params}")
logger.warning(f"Non-critical issue: {issue}")
logger.error(f"Error occurred: {error}", exc_info=True)
```

### 4. Result Format

Return consistent result format:

```python
{
    "status": "completed" | "failed",
    "tests_run": 0,
    "success_count": 0,
    "failure_count": 0,
    "errors": [],
    "metrics": {},
    "recommendations": []
}
```

## Troubleshooting

### Agent Not Running

**Issue:** Agent doesn't execute

**Solutions:**
1. Check agent is registered in `run_agents.py`
2. Verify `AgentType` enum includes your agent type
3. Check task dependencies are met
4. Review coordinator logs

### Database Lock Timeout

**Issue:** `TimeoutError: Could not acquire database lock`

**Solutions:**
1. Increase timeout in task configuration
2. Check for stuck locks in `agent_locks` table
3. Clean up expired locks manually

### Connection Errors

**Issue:** `ConnectionError` when testing API endpoints

**Solutions:**
1. Verify service is running on expected port
2. Check `base_url` in agent code
3. Ensure network connectivity

## Advanced Usage

### Custom Task Suites

```python
# tests/fixtures/custom_tasks.py
from tests.agents.coordinator import Task, AgentType

def get_custom_suite() -> List[Task]:
    return [
        Task(
            id="custom-1",
            agent_type=AgentType.API_TEST,
            description="Custom API test",
            priority=5,
            dependencies=[]
        ),
        # ... more tasks
    ]
```

### Parallel Execution Control

```bash
# Limit parallel agents
python -m tests.agents.run_agents --max-parallel 2

# Run sequentially
python -m tests.agents.run_agents --max-parallel 1
```

### Custom Report Output

```bash
# Specify output directory
python -m tests.agents.run_agents --output-dir /path/to/reports
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Agent Tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  agent-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd job-automation-service
          pip install -r requirements.txt
      - name: Run agents
        run: |
          cd job-automation-service
          python -m tests.agents.run_agents --suite quick
      - name: Upload reports
        uses: actions/upload-artifact@v2
        with:
          name: agent-reports
          path: job-automation-service/tests/agents/reports/
```

## See Also

- [Agent Framework Documentation](AGENT_FRAMEWORK.md)
- [API Documentation](API.md)
- [Remediation Guide](REMEDIATION_GUIDE.md)

