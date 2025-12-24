"""Validation script for agent framework."""

import asyncio
import logging
import sys
from pathlib import Path
from tests.agents.coordinator import AgentCoordinator, AgentType
from tests.agents.test_agents import api_test_agent, matcher_test_agent
from tests.agents.report_generator import ReportGenerator
from app.database import SessionLocal
from app.models.agent_task import AgentTask

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_single_agent():
    """Test coordinator with single agent."""
    logger.info("=" * 60)
    logger.info("Test 1: Single Agent Validation")
    logger.info("=" * 60)
    
    coordinator = AgentCoordinator(max_parallel=1)
    coordinator.register_agent(AgentType.API_TEST, api_test_agent)
    
    coordinator.add_task(
        task_id="test-single-api",
        agent_type=AgentType.API_TEST,
        description="Single agent test",
        dependencies=[],
        priority=5
    )
    
    await coordinator.run_agents()
    
    # Verify task completed
    db = SessionLocal()
    try:
        task = db.query(AgentTask).filter(AgentTask.id == "test-single-api").first()
        if task and task.status == "completed":
            logger.info("✓ Single agent test PASSED")
            return True
        else:
            logger.error(f"✗ Single agent test FAILED: status={task.status if task else 'not found'}")
            return False
    finally:
        db.close()


async def test_multi_agent():
    """Test coordinator with 2-3 agents in parallel."""
    logger.info("=" * 60)
    logger.info("Test 2: Multi-Agent (2-3 agents) Validation")
    logger.info("=" * 60)
    
    coordinator = AgentCoordinator(max_parallel=3)
    coordinator.register_agent(AgentType.API_TEST, api_test_agent)
    coordinator.register_agent(AgentType.MATCHER_TEST, matcher_test_agent)
    
    # Add independent tasks
    coordinator.add_task(
        task_id="test-multi-api-1",
        agent_type=AgentType.API_TEST,
        description="Multi agent test - API 1",
        dependencies=[],
        priority=5
    )
    
    coordinator.add_task(
        task_id="test-multi-api-2",
        agent_type=AgentType.API_TEST,
        description="Multi agent test - API 2",
        dependencies=[],
        priority=5
    )
    
    coordinator.add_task(
        task_id="test-multi-matcher",
        agent_type=AgentType.MATCHER_TEST,
        description="Multi agent test - Matcher",
        dependencies=[],
        priority=5
    )
    
    await coordinator.run_agents()
    
    # Verify all tasks completed
    db = SessionLocal()
    try:
        tasks = db.query(AgentTask).filter(
            AgentTask.id.in_(["test-multi-api-1", "test-multi-api-2", "test-multi-matcher"])
        ).all()
        
        completed = [t for t in tasks if t.status == "completed"]
        if len(completed) == len(tasks):
            logger.info(f"✓ Multi-agent test PASSED ({len(completed)}/{len(tasks)} completed)")
            return True
        else:
            logger.error(f"✗ Multi-agent test FAILED: {len(completed)}/{len(tasks)} completed")
            for task in tasks:
                if task.status != "completed":
                    logger.error(f"  - {task.id}: {task.status} - {task.error}")
            return False
    finally:
        db.close()


async def test_dependencies():
    """Test dependency resolution."""
    logger.info("=" * 60)
    logger.info("Test 3: Dependency Resolution")
    logger.info("=" * 60)
    
    coordinator = AgentCoordinator(max_parallel=2)
    coordinator.register_agent(AgentType.API_TEST, api_test_agent)
    coordinator.register_agent(AgentType.MATCHER_TEST, matcher_test_agent)
    
    # Task 1: No dependencies
    coordinator.add_task(
        task_id="test-dep-api",
        agent_type=AgentType.API_TEST,
        description="Dependency test - API",
        dependencies=[],
        priority=5
    )
    
    # Task 2: Depends on Task 1
    coordinator.add_task(
        task_id="test-dep-matcher",
        agent_type=AgentType.MATCHER_TEST,
        description="Dependency test - Matcher (depends on API)",
        dependencies=["test-dep-api"],
        priority=4
    )
    
    await coordinator.run_agents()
    
    # Verify execution order
    db = SessionLocal()
    try:
        api_task = db.query(AgentTask).filter(AgentTask.id == "test-dep-api").first()
        matcher_task = db.query(AgentTask).filter(AgentTask.id == "test-dep-matcher").first()
        
        if api_task and matcher_task:
            if api_task.started_at and matcher_task.started_at:
                if api_task.started_at < matcher_task.started_at:
                    logger.info("✓ Dependency resolution test PASSED (API started before Matcher)")
                    return True
                else:
                    logger.error("✗ Dependency resolution test FAILED (Matcher started before API)")
                    return False
            else:
                logger.error("✗ Dependency resolution test FAILED (missing timestamps)")
                return False
        else:
            logger.error("✗ Dependency resolution test FAILED (tasks not found)")
            return False
    finally:
        db.close()


async def test_report_generation():
    """Test report generation."""
    logger.info("=" * 60)
    logger.info("Test 4: Report Generation")
    logger.info("=" * 60)
    
    try:
        generator = ReportGenerator()
        reports = generator.generate_reports()
        
        if reports["markdown"].exists() and reports["json"].exists():
            logger.info(f"✓ Report generation test PASSED")
            logger.info(f"  Markdown: {reports['markdown']}")
            logger.info(f"  JSON: {reports['json']}")
            return True
        else:
            logger.error("✗ Report generation test FAILED (reports not created)")
            return False
    except Exception as e:
        logger.error(f"✗ Report generation test FAILED: {e}")
        return False


async def main():
    """Run all validation tests."""
    logger.info("Starting Agent Framework Validation")
    logger.info("")
    
    results = []
    
    # Test 1: Single agent
    try:
        result = await test_single_agent()
        results.append(("Single Agent", result))
    except Exception as e:
        logger.error(f"Single agent test error: {e}", exc_info=True)
        results.append(("Single Agent", False))
    
    logger.info("")
    
    # Test 2: Multi-agent
    try:
        result = await test_multi_agent()
        results.append(("Multi-Agent", result))
    except Exception as e:
        logger.error(f"Multi-agent test error: {e}", exc_info=True)
        results.append(("Multi-Agent", False))
    
    logger.info("")
    
    # Test 3: Dependencies
    try:
        result = await test_dependencies()
        results.append(("Dependencies", result))
    except Exception as e:
        logger.error(f"Dependency test error: {e}", exc_info=True)
        results.append(("Dependencies", False))
    
    logger.info("")
    
    # Test 4: Report generation
    try:
        result = await test_report_generation()
        results.append(("Report Generation", result))
    except Exception as e:
        logger.error(f"Report generation test error: {e}", exc_info=True)
        results.append(("Report Generation", False))
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Validation Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info("")
    logger.info(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✓ All validation tests PASSED")
        return 0
    else:
        logger.error("✗ Some validation tests FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

