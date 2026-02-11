"""Scheduler API endpoints for triggering job searches."""

import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel, field_validator
from typing import List, Optional
from app.models import User
from app.auth.oauth2 import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scheduler"])

# Global scheduler state
# Note: BackgroundTasks handles cleanup automatically, no need to track task
_scheduler_running = False
_current_config: Optional["ScheduledSearchRequest"] = None


class ScheduledSearchRequest(BaseModel):
    """Request schema for scheduled search."""
    queries: Optional[List[str]] = None
    location: str = "Minneapolis, MN"
    sources: Optional[List[str]] = None
    min_match_score: float = 0.7
    limit_per_query: int = 10
    
    @field_validator('min_match_score')
    @classmethod
    def validate_match_score(cls, v: float) -> float:
        """Validate min_match_score is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('min_match_score must be between 0.0 and 1.0')
        return v
    
    @field_validator('limit_per_query')
    @classmethod
    def validate_limit(cls, v: int) -> int:
        """Validate limit_per_query is between 1 and 100."""
        if v < 1 or v > 100:
            raise ValueError('limit_per_query must be between 1 and 100')
        return v
    
    @field_validator('location')
    @classmethod
    def validate_location(cls, v: str) -> str:
        """Validate location is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('location cannot be empty')
        return v.strip()
    
    @field_validator('queries')
    @classmethod
    def validate_queries(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate queries list is not empty if provided."""
        if v is not None and len(v) == 0:
            raise ValueError('queries list cannot be empty if provided')
        return v
    
    @field_validator('sources')
    @classmethod
    def validate_sources(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate sources list is not empty if provided."""
        if v is not None and len(v) == 0:
            raise ValueError('sources list cannot be empty if provided')
        return v


class SchedulerStatusResponse(BaseModel):
    """Scheduler status response model."""
    status: str  # "running" | "stopped"
    message: str
    location: Optional[str] = None
    min_match_score: Optional[float] = None
    queries: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    limit_per_query: Optional[int] = None


@router.post(
    "/start",
    response_model=SchedulerStatusResponse,
    responses={401: {"description": "Not authenticated"}, 500: {"description": "Failed to start scheduler"}},
)
async def start_scheduler(
    background_tasks: BackgroundTasks,
    request: ScheduledSearchRequest,
    current_user: User = Depends(get_current_user)
) -> SchedulerStatusResponse:
    """Start the scheduler for continuous job searches."""
    global _scheduler_running, _current_config
    
    if _scheduler_running:
        # Return current configuration if already running
        return {
            "message": "Scheduler is already running",
            "status": "running",
            "location": _current_config.location if _current_config else None,
            "min_match_score": _current_config.min_match_score if _current_config else None,
            "queries": _current_config.queries if _current_config else None,
            "sources": _current_config.sources if _current_config else None,
            "limit_per_query": _current_config.limit_per_query if _current_config else None
        }
    
    try:
        # Note: In a full implementation, this would start the actual scheduler
        # For now, we mark it as running and could proxy to job-automation-service
        # or implement the scheduler logic here
        
        # Start scheduler in background (placeholder for actual scheduler logic)
        def _scheduler_worker():
            """Background worker for scheduler."""
            global _scheduler_running
            try:
                # Placeholder: Actual scheduler would run periodic searches here
                logger.info(f"Scheduler started with location: {request.location}")
                # In a real implementation, this would call the job search service
                # For now, we just mark it as running
                pass
            except Exception as e:
                logger.error(f"Scheduler worker error: {e}")
                _scheduler_running = False
        
        # Add background task
        background_tasks.add_task(_scheduler_worker)
        
        # Store current configuration
        _current_config = request
        _scheduler_running = True
        
        return {
            "message": "Scheduler started",
            "status": "running",
            "location": request.location,
            "min_match_score": request.min_match_score,
            "queries": request.queries,
            "sources": request.sources,
            "limit_per_query": request.limit_per_query
        }
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        _scheduler_running = False
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/status",
    response_model=SchedulerStatusResponse,
    responses={401: {"description": "Not authenticated"}},
)
async def get_scheduler_status(
    current_user: User = Depends(get_current_user)
) -> SchedulerStatusResponse:
    """Get current scheduler status."""
    global _scheduler_running, _current_config
    
    if _scheduler_running and _current_config:
        return {
            "status": "running",
            "message": "Scheduler is running",
            "location": _current_config.location,
            "min_match_score": _current_config.min_match_score,
            "queries": _current_config.queries,
            "sources": _current_config.sources,
            "limit_per_query": _current_config.limit_per_query
        }
    else:
        return {
            "status": "stopped",
            "message": "Scheduler is stopped"
        }


@router.post(
    "/stop",
    response_model=SchedulerStatusResponse,
    responses={401: {"description": "Not authenticated"}, 500: {"description": "Failed to stop scheduler"}},
)
async def stop_scheduler(
    current_user: User = Depends(get_current_user)
) -> SchedulerStatusResponse:
    """Stop the scheduler."""
    global _scheduler_running, _current_config
    
    if not _scheduler_running:
        return {
            "message": "Scheduler is not running",
            "status": "stopped"
        }
    
    try:
        # BackgroundTasks handles cleanup automatically
        _scheduler_running = False
        _current_config = None
        
        logger.info("Scheduler stopped successfully")
        
        return {
            "message": "Scheduler stopped",
            "status": "stopped"
        }
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

