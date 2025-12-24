"""Main script to run parallel agents for testing and gap analysis."""

import asyncio
import argparse
import logging
import os
import sys
from pathlib import Path

# Set default DATABASE_URL before importing anything that uses the database
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql://jobautomation:password@localhost:5433/jobautomation"

from tests.agents.coordinator import AgentCoordinator, AgentType
from tests.agents.test_agents import (
    scraper_test_agent,
    matcher_test_agent,
    api_test_agent,
    cover_letter_test_agent,
    scheduler_test_agent
)
from tests.agents.gap_analysis_agents import (
    gap_analysis_agent,
    performance_analysis_agent,
    security_analysis_agent,
    documentation_analysis_agent,
    compliance_analysis_agent
)
from tests.agents.integration_test_agent import integration_test_agent
from tests.agents.performance_benchmark_agent import performance_benchmark_agent
from tests.agents.regression_test_agent import regression_test_agent
from tests.agents.report_generator import ReportGenerator
from tests.fixtures.agent_tasks import (
    get_quick_test_suite,
    get_full_test_suite,
    get_gap_analysis_suite,
    get_performance_suite,
    build_custom_suite
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run multi-agent testing and gap analysis"
    )
    
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Override database URL (defaults to DATABASE_URL env var or localhost:5433)"
    )
    
    parser.add_argument(
        "--agents",
        nargs="+",
        choices=[at.value for at in AgentType],
        help="Specific agents to run"
    )
    
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=None,
        help="Maximum parallel agents (default: 3)"
    )
    
    parser.add_argument(
        "--suite",
        choices=["quick", "full", "gap", "performance", "custom"],
        default="full",
        help="Predefined test suite"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Report output directory"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


async def main():
    """Main execution function."""
    args = parse_args()
    
    # Override DATABASE_URL if provided via command line
    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url
        logger.info(f"Using provided DATABASE_URL: {args.database_url}")
    elif not os.getenv("DATABASE_URL"):
        default_db_url = "postgresql://jobautomation:password@localhost:5433/jobautomation"
        os.environ["DATABASE_URL"] = default_db_url
        logger.info(f"Using default DATABASE_URL: {default_db_url}")
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting Multi-Agent Testing and Gap Analysis Framework")
    
    # Initialize coordinator
    coordinator = AgentCoordinator(max_parallel=args.max_parallel)
    
    # Register all agents
    coordinator.register_agent(AgentType.SCRAPER_TEST, scraper_test_agent)
    coordinator.register_agent(AgentType.MATCHER_TEST, matcher_test_agent)
    coordinator.register_agent(AgentType.API_TEST, api_test_agent)
    coordinator.register_agent(AgentType.COVER_LETTER_TEST, cover_letter_test_agent)
    coordinator.register_agent(AgentType.SCHEDULER_TEST, scheduler_test_agent)
    coordinator.register_agent(AgentType.GAP_ANALYSIS, gap_analysis_agent)
    coordinator.register_agent(AgentType.PERFORMANCE_ANALYSIS, performance_analysis_agent)
    coordinator.register_agent(AgentType.SECURITY_ANALYSIS, security_analysis_agent)
    coordinator.register_agent(AgentType.DOC_ANALYSIS, documentation_analysis_agent)
    coordinator.register_agent(AgentType.COMPLIANCE_ANALYSIS, compliance_analysis_agent)
    
    # Register new agents if available
    try:
        coordinator.register_agent(AgentType("integration_test"), integration_test_agent)
    except:
        pass  # Agent type not in enum yet
    
    try:
        coordinator.register_agent(AgentType("performance_benchmark"), performance_benchmark_agent)
    except:
        pass
    
    try:
        coordinator.register_agent(AgentType("regression_test"), regression_test_agent)
    except:
        pass
    
    # Get task suite
    if args.suite == "quick":
        tasks = get_quick_test_suite()
    elif args.suite == "full":
        tasks = get_full_test_suite()
    elif args.suite == "gap":
        tasks = get_gap_analysis_suite()
    elif args.suite == "performance":
        tasks = get_performance_suite()
    else:  # custom
        if args.agents:
            agent_types = [AgentType(at) for at in args.agents]
            tasks = build_custom_suite(agent_types)
        else:
            logger.error("--agents required for custom suite")
            sys.exit(1)
    
    # Filter tasks if specific agents requested
    if args.agents:
        agent_set = set(args.agents)
        tasks = [t for t in tasks if t["agent_type"].value in agent_set]
    
    if not tasks:
        logger.error("No tasks to run")
        sys.exit(1)
    
    # Add tasks to coordinator
    logger.info(f"Adding {len(tasks)} tasks to coordinator")
    for task_def in tasks:
        coordinator.add_task(
            task_id=task_def["id"],
            agent_type=task_def["agent_type"],
            description=task_def["description"],
            dependencies=task_def.get("dependencies", []),
            priority=task_def.get("priority", 0),
            timeout=task_def.get("timeout", None)
        )
    
    # Run agents
    try:
        await coordinator.run_agents()
        logger.info("All agents completed")
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running agents: {e}", exc_info=True)
        sys.exit(1)
    
    # Generate reports
    try:
        logger.info("Generating reports...")
        output_dir = Path(args.output) if args.output else None
        generator = ReportGenerator(output_dir=output_dir)
        reports = generator.generate_reports()
        
        logger.info(f"Reports generated:")
        logger.info(f"  Markdown: {reports['markdown']}")
        logger.info(f"  JSON: {reports['json']}")
        
    except Exception as e:
        logger.error(f"Error generating reports: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())


