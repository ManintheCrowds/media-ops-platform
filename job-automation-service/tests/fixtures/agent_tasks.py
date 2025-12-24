"""Predefined task sets for agent execution."""

from typing import List, Dict
from tests.agents.coordinator import AgentType


def get_quick_test_suite() -> List[Dict]:
    """Get quick test suite with minimal tasks."""
    return [
        {
            "id": "test-api-quick",
            "agent_type": AgentType.API_TEST,
            "description": "Quick API test",
            "dependencies": [],
            "priority": 5
        },
        {
            "id": "test-matcher-quick",
            "agent_type": AgentType.MATCHER_TEST,
            "description": "Quick matcher test",
            "dependencies": [],
            "priority": 5
        }
    ]


def get_full_test_suite() -> List[Dict]:
    """Get full test suite with all agents."""
    return [
        # Testing tasks (can run in parallel)
        {
            "id": "test-scraper-indeed",
            "agent_type": AgentType.SCRAPER_TEST,
            "description": "Test job scrapers",
            "dependencies": [],
            "priority": 5
        },
        {
            "id": "test-matcher",
            "agent_type": AgentType.MATCHER_TEST,
            "description": "Test skills matching",
            "dependencies": [],
            "priority": 5
        },
        {
            "id": "test-api",
            "agent_type": AgentType.API_TEST,
            "description": "Test API endpoints",
            "dependencies": [],
            "priority": 5
        },
        {
            "id": "test-cover-letter",
            "agent_type": AgentType.COVER_LETTER_TEST,
            "description": "Test cover letter generation",
            "dependencies": ["test-matcher"],  # Needs matcher to work
            "priority": 4
        },
        {
            "id": "test-scheduler",
            "agent_type": AgentType.SCHEDULER_TEST,
            "description": "Test scheduler functionality",
            "dependencies": [],
            "priority": 4
        },
        
        # Analysis tasks (can run after testing)
        {
            "id": "gap-analysis",
            "agent_type": AgentType.GAP_ANALYSIS,
            "description": "Gap analysis",
            "dependencies": ["test-api"],  # Needs API to be tested
            "priority": 3
        },
        {
            "id": "performance-analysis",
            "agent_type": AgentType.PERFORMANCE_ANALYSIS,
            "description": "Performance analysis",
            "dependencies": ["test-api"],
            "priority": 3
        },
        {
            "id": "security-analysis",
            "agent_type": AgentType.SECURITY_ANALYSIS,
            "description": "Security analysis",
            "dependencies": [],
            "priority": 4
        },
        {
            "id": "doc-analysis",
            "agent_type": AgentType.DOC_ANALYSIS,
            "description": "Documentation analysis",
            "dependencies": [],
            "priority": 2
        },
        {
            "id": "compliance-analysis",
            "agent_type": AgentType.COMPLIANCE_ANALYSIS,
            "description": "Compliance analysis",
            "dependencies": [],
            "priority": 3
        },
    ]


def get_gap_analysis_suite() -> List[Dict]:
    """Get gap analysis only suite."""
    return [
        {
            "id": "gap-analysis",
            "agent_type": AgentType.GAP_ANALYSIS,
            "description": "Gap analysis",
            "dependencies": [],
            "priority": 5
        },
        {
            "id": "doc-analysis",
            "agent_type": AgentType.DOC_ANALYSIS,
            "description": "Documentation analysis",
            "dependencies": [],
            "priority": 4
        },
        {
            "id": "compliance-analysis",
            "agent_type": AgentType.COMPLIANCE_ANALYSIS,
            "description": "Compliance analysis",
            "dependencies": [],
            "priority": 4
        }
    ]


def get_performance_suite() -> List[Dict]:
    """Get performance test suite."""
    return [
        {
            "id": "test-api",
            "agent_type": AgentType.API_TEST,
            "description": "Test API endpoints",
            "dependencies": [],
            "priority": 5
        },
        {
            "id": "performance-analysis",
            "agent_type": AgentType.PERFORMANCE_ANALYSIS,
            "description": "Performance analysis",
            "dependencies": ["test-api"],
            "priority": 5
        }
    ]


def build_custom_suite(agent_types: List[AgentType], dependencies: Dict[str, List[str]] = None) -> List[Dict]:
    """Build custom task suite.
    
    Args:
        agent_types: List of agent types to include
        dependencies: Optional dictionary mapping task IDs to dependency lists
        
    Returns:
        List of task definitions
    """
    tasks = []
    deps = dependencies or {}
    
    for i, agent_type in enumerate(agent_types):
        task_id = f"custom-{agent_type.value}-{i}"
        tasks.append({
            "id": task_id,
            "agent_type": agent_type,
            "description": f"Custom {agent_type.value} task",
            "dependencies": deps.get(task_id, []),
            "priority": 5
        })
    
    return tasks


