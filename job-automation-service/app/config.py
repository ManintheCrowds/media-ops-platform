"""Configuration management for the job automation service."""

from pydantic_settings import BaseSettings
from typing import Optional, List
from pathlib import Path
import os
from dotenv import load_dotenv


def _find_env_file() -> str:
    """Find .env file in current directory or parent directory.
    
    Returns:
        Absolute path to .env file or ".env" if not found
    """
    # Primary location: D:\software\job-automation-service\.env
    # This is the canonical location for the .env file
    primary_env = Path(r"D:\software\job-automation-service\.env")
    if primary_env.exists():
        return str(primary_env.absolute())
    
    # Fallback: Check current directory (job-automation-service)
    current_dir = Path(__file__).parent.parent
    env_file = current_dir / ".env"
    if env_file.exists():
        return str(env_file.absolute())
    
    # Fallback: Check parent directory (software)
    parent_dir = current_dir.parent
    env_file = parent_dir / ".env"
    if env_file.exists():
        return str(env_file.absolute())
    
    # Fallback: Check C:\Users\artin\software\.env directly (for Windows)
    if os.name == 'nt':  # Windows
        software_env = Path("C:/Users/artin/software/.env")
        if software_env.exists():
            return str(software_env.absolute())
    
    # Default to .env in current directory (relative path)
    return ".env"


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Job Application Automation Service"
    app_version: str = "0.1.0"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    
    # Database
    # Default to localhost:5433 for local development (Docker Compose exposes on 5433)
    # Override with DATABASE_URL env var
    database_url: str = "postgresql://jobautomation:password@localhost:5433/jobautomation"
    
    # Platform Integration
    platform_url: str = "http://platform:8000"
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    
    # Job Sources - API Keys (optional, for future API integrations)
    indeed_api_key: Optional[str] = None
    linkedin_api_key: Optional[str] = None
    glassdoor_api_key: Optional[str] = None
    ziprecruiter_api_key: Optional[str] = None
    adzuna_api_key: Optional[str] = None
    adzuna_api_id: Optional[str] = None
    the_muse_api_key: Optional[str] = None
    jsearch_api_key: Optional[str] = None
    
    # Browser Scraping Configuration
    use_browser_scraping: bool = True
    browser_type: str = "playwright"  # or "selenium"
    headless: bool = True
    browser_timeout: int = 30
    stealth_mode: bool = True
    
    # Ollama Configuration
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"  # Default model, can be changed
    
    # Rate Limiting
    scraper_delay_min: float = 2.0  # Minimum seconds between requests
    scraper_delay_max: float = 8.0  # Maximum seconds between requests (increased from 5.0)
    use_human_delays: bool = True
    enable_referer_chain: bool = True
    cookie_persistence: bool = True
    max_retries: int = 3
    
    # Proxy Configuration (Future Enhancement)
    proxy_enabled: bool = False
    proxy_list: List[str] = []
    proxy_rotation_strategy: str = "round_robin"  # Options: "round_robin", "random", "least_used"
    
    # Debug Logging
    debug_log_path: Optional[str] = None  # Path to debug log file (optional, defaults to None for no logging)
    
    # Default Search Parameters
    default_location: str = "Minneapolis, MN"
    default_radius: int = 25  # miles
    
    # CORS
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    class Config:
        env_file = _find_env_file()
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = "ignore"


# Explicitly load .env file BEFORE creating Settings instance
# This ensures environment variables are available to pydantic_settings
_env_file_path = _find_env_file()
if Path(_env_file_path).exists():
    load_dotenv(_env_file_path, override=True)
    print(f"[CONFIG] Loaded .env file from: {_env_file_path}")
else:
    print(f"[CONFIG] WARNING: .env file not found at: {_env_file_path}")
    # Try loading from default location as fallback
    default_env = Path(__file__).parent.parent / ".env"
    if default_env.exists():
        load_dotenv(default_env, override=True)
        print(f"[CONFIG] Loaded .env file from fallback: {default_env}")


settings = Settings()

