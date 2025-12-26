"""Scheduler API endpoints for triggering job searches."""

import logging
import asyncio
from fastapi import APIRouter, BackgroundTasks, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
from app.services.scheduler import run_scheduled_search, run_daily_search, run_weekly_search

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scheduler", tags=["scheduler"])

# Global scheduler state
_scheduler_running = False
_scheduler_task = None


class ScheduledSearchRequest(BaseModel):
    """Request schema for scheduled search."""
    queries: Optional[List[str]] = None
    location: str = "Minneapolis, MN"
    sources: Optional[List[str]] = None
    min_match_score: float = 0.7
    limit_per_query: int = 10


@router.post("/search")
async def trigger_search(
    request: ScheduledSearchRequest,
    background_tasks: BackgroundTasks
):
    """Trigger a job search in the background."""
    try:
        background_tasks.add_task(
            run_scheduled_search,
            queries=request.queries,
            location=request.location,
            sources=request.sources,
            min_match_score=request.min_match_score,
            limit_per_query=request.limit_per_query
        )
        return {
            "message": "Job search started in background",
            "location": request.location,
            "min_match_score": request.min_match_score
        }
    except Exception as e:
        logger.error(f"Error triggering search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/daily")
async def trigger_daily_search(background_tasks: BackgroundTasks):
    """Trigger daily job search."""
    try:
        background_tasks.add_task(run_daily_search)
        return {"message": "Daily job search started in background"}
    except Exception as e:
        logger.error(f"Error triggering daily search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weekly")
async def trigger_weekly_search(background_tasks: BackgroundTasks):
    """Trigger weekly job search."""
    try:
        background_tasks.add_task(run_weekly_search)
        return {"message": "Weekly job search started in background"}
    except Exception as e:
        logger.error(f"Error triggering weekly search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_scheduler(
    background_tasks: BackgroundTasks,
    request: Optional[ScheduledSearchRequest] = Body(default=None)
):
    """Start the scheduler for continuous job searches."""
    global _scheduler_running, _scheduler_task
    
    if _scheduler_running:
        return {
            "message": "Scheduler is already running",
            "status": "running"
        }
    
    try:
        # Use defaults if request is None
        if request is None:
            request = ScheduledSearchRequest()
        
        # Start scheduler in background
        background_tasks.add_task(
            run_scheduled_search,
            queries=request.queries,
            location=request.location,
            sources=request.sources,
            min_match_score=request.min_match_score,
            limit_per_query=request.limit_per_query
        )
        
        _scheduler_running = True
        
        return {
            "message": "Scheduler started",
            "status": "running",
            "location": request.location,
            "min_match_score": request.min_match_score
        }
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        _scheduler_running = False
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_scheduler():
    """Stop the scheduler."""
    global _scheduler_running, _scheduler_task
    
    if not _scheduler_running:
        return {
            "message": "Scheduler is not running",
            "status": "stopped"
        }
    
    try:
        # Cancel task if running
        if _scheduler_task and not _scheduler_task.done():
            _scheduler_task.cancel()
            try:
                await _scheduler_task
            except asyncio.CancelledError:
                pass
        
        _scheduler_running = False
        _scheduler_task = None
        
        return {
            "message": "Scheduler stopped",
            "status": "stopped"
        }
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

