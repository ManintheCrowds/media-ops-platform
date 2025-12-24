"""Configuration for agent framework."""

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class AgentConfig(BaseSettings):
    """Agent framework configuration."""
    
    # Parallel execution
    max_parallel_agents: int = 3  # Following scope-before-scale principle
    
    # Timeouts
    default_task_timeout: int = 300  # seconds
    lock_timeout: int = 60  # seconds to wait for lock
    lock_expiration: int = 600  # seconds before lock expires
    
    # Database (for coordination)
    database_url: Optional[str] = None  # Will use app config if None
    
    # Report paths
    report_output_dir: Path = Path("tests/agents/reports")
    status_file: Path = Path("tests/agents/status/status.json")
    lock_dir: Path = Path("tests/agents/locks")  # Fallback file locks
    
    # Agent settings
    enable_file_lock_fallback: bool = True  # Use file locks if DB unavailable
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


config = AgentConfig()


