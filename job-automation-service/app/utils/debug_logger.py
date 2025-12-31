"""Debug logging utility for pipeline tracking."""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Debug log path (can be overridden via environment)
DEBUG_LOG_PATH = Path(__file__).parent.parent.parent / "debug.log"


def _is_debug_enabled() -> bool:
    """Check if debug logging is enabled via settings."""
    try:
        from app.config import settings
        return settings.debug
    except Exception:
        # If settings not available, default to False for production safety
        return False


def ensure_debug_log_dir() -> None:
    """Ensure debug log directory exists."""
    try:
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.debug(f"Failed to create debug log directory: {e}")


def log_pipeline_event(
    session_id: str,
    hypothesis_id: str,
    location: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    write_to_file: Optional[bool] = None
) -> None:
    """Log a pipeline event to both logger and debug file.
    
    Args:
        session_id: Session identifier
        hypothesis_id: Hypothesis identifier for tracking
        location: Code location (e.g., "jobs.py:search_jobs")
        message: Event message
        data: Additional data to log
        write_to_file: Whether to write to debug.log file (None = use settings.debug)
    """
    # Only log if debug is enabled
    if not _is_debug_enabled():
        return
    
    log_entry = {
        "sessionId": session_id,
        "runId": f"{session_id}-{int(time.time())}",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000)
    }
    
    # Log to standard logger
    logger.debug(f"[{hypothesis_id}] {message}", extra={"data": data, "location": location})
    
    # Optionally write to debug file (defaults to settings.debug if not specified)
    should_write = write_to_file if write_to_file is not None else _is_debug_enabled()
    if should_write:
        try:
            ensure_debug_log_dir()
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.debug(f"Failed to write debug log entry: {e}")


def log_pipeline_start(
    location: str,
    query: str,
    location_str: Optional[str] = None,
    sources: Optional[list] = None,
    limit: Optional[int] = None,
    min_match_score: Optional[float] = None
) -> None:
    """Log pipeline start event."""
    log_pipeline_event(
        session_id="pipeline-debug",
        hypothesis_id="H0",
        location=location,
        message="Starting job search pipeline",
        data={
            "query": query,
            "location": location_str or "Minneapolis, MN",
            "sources": sources or ["indeed", "linkedin", "glassdoor", "ziprecruiter"],
            "limit": limit or 25,
            "min_match_score": min_match_score,
        }
    )

