"""Job search and listing API endpoints."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.database import get_db
from app.models.job_listing import JobListing
from app.schemas.job import (
    JobListingResponse,
    JobSearchRequest,
    JobSearchResponse,
    JobListingCreate
)
from app.services.job_source_manager import JobSourceManager
from app.services.skill_matcher import SkillMatcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

# Supported sources (including aggregator APIs)
SUPPORTED_SOURCES = [
    "indeed", "linkedin", "glassdoor", "ziprecruiter",
    "adzuna", "the_muse", "jsearch"
]


@router.post("/search", response_model=JobSearchResponse)
async def search_jobs(
    request: JobSearchRequest,
    db: Session = Depends(get_db)
):
    """Search for jobs across multiple sources."""
    # #region agent log
    import json
    import time
    from pathlib import Path
    debug_log_path = Path("C:/Users/artin/software/.cursor/debug.log")
    pipeline_start_time = time.time()
    try:
        log_entry = {
            "sessionId": "pipeline-debug",
            "runId": f"pipeline-{int(time.time())}",
            "hypothesisId": "H0",
            "location": "jobs.py:search_jobs",
            "message": "Starting job search pipeline",
            "data": {
                "query": request.query,
                "location": request.location or "Minneapolis, MN",
                "sources": request.sources or ["indeed", "linkedin", "glassdoor", "ziprecruiter"],
                "limit": request.limit or 25,
                "min_match_score": request.min_match_score,
            },
            "timestamp": int(time.time() * 1000)
        }
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    # #endregion agent log
    
    location = request.location or "Minneapolis, MN"
    sources = request.sources or ["adzuna", "indeed", "linkedin", "glassdoor", "ziprecruiter"]
    
    # Filter to supported sources
    sources = [s for s in sources if s in SUPPORTED_SOURCES]
    
    # Log filtering result
    print(f"[DEBUG] After filtering, sources: {sources}, SUPPORTED_SOURCES: {SUPPORTED_SOURCES}")  # Console output
    logger.info(f"Filtered sources: {sources}")
    
    if not sources:
        logger.warning("No supported sources after filtering")
        print(f"[DEBUG] No supported sources! Request sources: {request.sources}, SUPPORTED: {SUPPORTED_SOURCES}")  # Console output
        return JobSearchResponse(
            jobs=[],
            count=0,
            sources_searched=[]
        )
    
    all_jobs = []
    sources_searched = []
    
    # Use JobSourceManager for multi-strategy search
    print(f"[DEBUG] Creating JobSourceManager...")  # Console output
    try:
        source_manager = JobSourceManager()
        print(f"[DEBUG] JobSourceManager created successfully")  # Console output
    except Exception as e:
        print(f"[DEBUG] Failed to create JobSourceManager: {e}")  # Console output
        logger.error(f"Failed to create JobSourceManager: {e}", exc_info=True)
        raise
    
    try:
        # Search all sources using fallback chain (API → Browser → HTTP)
        logger.info(f"Starting search with sources: {sources}, query: {request.query}")
        print(f"[DEBUG] Starting search with sources: {sources}, query: {request.query}")  # Console output
        
        # #region agent log
        try:
            log_entry = {
                "sessionId": "endpoint-debug",
                "runId": f"endpoint-{int(time.time())}",
                "hypothesisId": "H-ENDPOINT",
                "location": "jobs.py:search_jobs",
                "message": "About to call source_manager.search_jobs",
                "data": {
                    "query": request.query,
                    "location": location,
                    "sources": sources,
                    "limit": request.limit or 25,
                },
                "timestamp": int(time.time() * 1000)
            }
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
            print(f"[DEBUG] Logged: About to call source_manager.search_jobs")  # Console output
        except Exception as log_err:
            print(f"[DEBUG] Failed to write log: {log_err}")  # Console output
            pass
        # #endregion agent log
        
        try:
            print(f"[DEBUG] Calling source_manager.search_jobs with sources: {sources}")  # Console output
            all_jobs = await source_manager.search_jobs(
                query=request.query,
                location=location,
                sources=sources,
                limit=request.limit or 25
            )
            print(f"[DEBUG] source_manager.search_jobs returned {len(all_jobs)} jobs")  # Console output
            sources_searched = sources
            logger.info(f"Found {len(all_jobs)} jobs from sources: {sources}")
            
            # #region agent log
            try:
                log_entry = {
                    "sessionId": "endpoint-debug",
                    "runId": f"endpoint-{int(time.time())}",
                    "hypothesisId": "H-ENDPOINT",
                    "location": "jobs.py:search_jobs",
                    "message": "source_manager.search_jobs completed",
                    "data": {
                        "jobs_found": len(all_jobs),
                        "sources_searched": sources_searched,
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
            # #endregion agent log
            
        except Exception as e:
            # Log to both logger and console for visibility
            error_msg = f"Error in source_manager.search_jobs: {type(e).__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"[ENDPOINT ERROR] {error_msg}")  # Also print to console
            print(f"[ENDPOINT ERROR] Full error: {e}")  # Also print to console
            logger.error(f"Error in source_manager.search_jobs: {e}", exc_info=True)
            # Log the full exception for debugging
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Traceback: {error_trace}")
            print(f"[ENDPOINT ERROR] Traceback:\n{error_trace}")  # Also print to console
            # Also log to debug file
            try:
                log_entry = {
                    "sessionId": "pipeline-debug",
                    "runId": f"pipeline-{int(time.time())}",
                    "hypothesisId": "H-ERROR",
                    "location": "jobs.py:search_jobs",
                    "message": "Exception in source_manager.search_jobs",
                    "data": {
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "traceback": error_trace,
                        "sources": sources,
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
                print(f"[DEBUG] Error logged to debug file")  # Console output
            except Exception as log_err:
                print(f"[DEBUG] Failed to write error log: {log_err}")  # Console output
                pass
            all_jobs = []
            sources_searched = []
        
        # #region agent log
        try:
            log_entry = {
                "sessionId": "pipeline-debug",
                "runId": f"pipeline-{int(time.time())}",
                "hypothesisId": "H3",
                "location": "jobs.py:search_jobs",
                "message": "Starting job matching and scoring",
                "data": {
                    "total_jobs_found": len(all_jobs),
                    "sources_searched": sources_searched,
                },
                "timestamp": int(time.time() * 1000)
            }
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
        # #endregion agent log
        
        # Match and score jobs
        try:
            matcher = SkillMatcher(db)
        except Exception as e:
            logger.error(f"Error creating SkillMatcher: {e}", exc_info=True)
            print(f"[ENDPOINT ERROR] Error creating SkillMatcher: {e}")
            # If matcher fails, return jobs without scoring
            matched_jobs = []
            for job_data in all_jobs:
                # Create job listing without scoring
                existing = db.query(JobListing).filter(
                    JobListing.source == job_data.get("source", ""),
                    JobListing.source_id == job_data.get("source_id")
                ).first()
                
                if not existing:
                    job_listing = JobListing(
                        title=job_data.get("title", ""),
                        company=job_data.get("company", ""),
                        location=job_data.get("location"),
                        source=job_data.get("source", ""),
                        source_id=job_data.get("source_id"),
                        url=job_data.get("url", ""),
                        description=job_data.get("description"),
                    )
                    db.add(job_listing)
                    matched_jobs.append(job_listing)
                else:
                    matched_jobs.append(existing)
            
            db.commit()
            job_responses = [JobListingResponse.from_orm(job) for job in matched_jobs]
            return JobSearchResponse(
                jobs=job_responses,
                count=len(job_responses),
                sources_searched=sources_searched
            )
        
        matched_jobs = []
        new_jobs_count = 0
        updated_jobs_count = 0
        
        try:
            for job_data in all_jobs:
                # Validate required fields
                source = job_data.get("source", "").strip()
                source_id = job_data.get("source_id", "").strip() if job_data.get("source_id") else None
                title = job_data.get("title", "").strip()
                company = job_data.get("company", "").strip()
                url = job_data.get("url", "").strip()
                
                # Skip jobs with missing required fields
                if not source or not title or not company or not url:
                    logger.warning(f"Skipping job with missing required fields: source={source}, title={title}, company={company}, url={url}")
                    continue
                
                # Check if job already exists - use proper query with and_ for multiple conditions
                query = db.query(JobListing).filter(JobListing.source == source)
                if source_id:
                    query = query.filter(JobListing.source_id == source_id)
                else:
                    # If no source_id, also match by title, company, and url to avoid duplicates
                    query = query.filter(
                        and_(
                            JobListing.title == title,
                            JobListing.company == company,
                            JobListing.url == url
                        )
                    )
                existing = query.first()
                
                if existing:
                    # Update existing job
                    job_listing = existing
                    # Update fields that might have changed
                    if job_data.get("description"):
                        job_listing.description = job_data.get("description")
                    if job_data.get("requirements"):
                        job_listing.requirements = job_data.get("requirements")
                    if job_data.get("salary_range"):
                        job_listing.salary_range = job_data.get("salary_range")
                    if job_data.get("job_type"):
                        job_listing.job_type = job_data.get("job_type")
                    if "remote" in job_data:
                        job_listing.remote = job_data.get("remote", False)
                    if job_data.get("raw_data"):
                        job_listing.raw_data = job_data.get("raw_data")
                    updated_jobs_count += 1
                else:
                    # Create new job listing
                    job_listing = JobListing(
                        title=title,
                        company=company,
                        location=job_data.get("location"),
                        source=source,
                        source_id=source_id,
                        url=url,
                        description=job_data.get("description"),
                        requirements=job_data.get("requirements"),
                        salary_range=job_data.get("salary_range"),
                        job_type=job_data.get("job_type"),
                        remote=job_data.get("remote", False),
                        raw_data=job_data.get("raw_data"),
                    )
                    db.add(job_listing)
                    new_jobs_count += 1
                
                # Calculate match scores
                description = job_listing.description or ""
                try:
                    scores = matcher.calculate_match_score(description)
                    job_listing.skill_match_score = scores.get("skill_match_score", 0.0)
                    job_listing.experience_match_score = scores.get("experience_match_score", 0.0)
                    job_listing.overall_match_score = scores.get("overall_match_score", 0.0)
                except Exception as score_error:
                    logger.error(f"Error calculating match score for job {title}: {score_error}", exc_info=True)
                    # Set default scores if matching fails
                    job_listing.skill_match_score = 0.0
                    job_listing.experience_match_score = 0.0
                    job_listing.overall_match_score = 0.0
                
                # Only include if meets minimum score
                if job_listing.overall_match_score >= request.min_match_score:
                    matched_jobs.append(job_listing)
        except Exception as e:
            logger.error(f"Error processing jobs: {e}", exc_info=True)
            print(f"[ENDPOINT ERROR] Error processing jobs: {e}")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Traceback: {error_trace}")
            # Log to debug file
            try:
                log_entry = {
                    "sessionId": "pipeline-debug",
                    "runId": f"pipeline-{int(time.time())}",
                    "hypothesisId": "H-ERROR-PROCESSING",
                    "location": "jobs.py:search_jobs",
                    "message": "Exception processing jobs",
                    "data": {
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "traceback": error_trace,
                        "jobs_processed": len(matched_jobs),
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
            # Rollback on error
            db.rollback()
            # Return empty result since processing failed
            return JobSearchResponse(
                jobs=[],
                count=0,
                sources_searched=sources_searched
            )
        
        # Flush to catch validation errors before commit
        try:
            db.flush()
        except Exception as e:
            logger.error(f"Error flushing to database: {e}", exc_info=True)
            print(f"[ENDPOINT ERROR] Database flush failed: {e}")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Traceback: {error_trace}")
            db.rollback()
            # Log to debug file
            try:
                log_entry = {
                    "sessionId": "pipeline-debug",
                    "runId": f"pipeline-{int(time.time())}",
                    "hypothesisId": "H-ERROR-FLUSH",
                    "location": "jobs.py:search_jobs",
                    "message": "Exception flushing to database",
                    "data": {
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "traceback": error_trace,
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
            # Return empty result since flush failed
            return JobSearchResponse(
                jobs=[],
                count=0,
                sources_searched=sources_searched
            )
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error committing to database: {e}", exc_info=True)
            print(f"[ENDPOINT ERROR] Database commit failed: {e}")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Traceback: {error_trace}")
            db.rollback()
            # Log to debug file
            try:
                log_entry = {
                    "sessionId": "pipeline-debug",
                    "runId": f"pipeline-{int(time.time())}",
                    "hypothesisId": "H-ERROR-COMMIT",
                    "location": "jobs.py:search_jobs",
                    "message": "Exception committing to database",
                    "data": {
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "traceback": error_trace,
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
            # Return empty result since commit failed
            return JobSearchResponse(
                jobs=[],
                count=0,
                sources_searched=sources_searched
            )
        
        # #region agent log
        pipeline_elapsed = time.time() - pipeline_start_time
        try:
            log_entry = {
                "sessionId": "pipeline-debug",
                "runId": f"pipeline-{int(time.time())}",
                "hypothesisId": "H4",
                "location": "jobs.py:search_jobs",
                "message": "Completed job search pipeline",
                "data": {
                    "total_jobs_found": len(all_jobs),
                    "new_jobs_saved": new_jobs_count,
                    "existing_jobs_updated": updated_jobs_count,
                    "matched_jobs_count": len(matched_jobs),
                    "sources_searched": sources_searched,
                    "elapsed_time_ms": round(pipeline_elapsed * 1000, 2),
                    "min_match_score": request.min_match_score,
                },
                "timestamp": int(time.time() * 1000)
            }
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
        # #endregion agent log
        
        # Convert to response models
        job_responses = [JobListingResponse.from_orm(job) for job in matched_jobs]
        
        return JobSearchResponse(
            jobs=job_responses,
            count=len(job_responses),
            sources_searched=sources_searched
        )
        
    finally:
        # Cleanup source manager
        try:
            await source_manager.close()
        except Exception as e:
            logger.warning(f"Error closing source manager: {e}")


@router.get("", response_model=List[JobListingResponse])
async def list_jobs(
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    source: Optional[str] = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List saved job listings with filtering."""
    query = db.query(JobListing)
    
    if active_only:
        query = query.filter(JobListing.is_active == True)
    
    if min_score is not None:
        query = query.filter(JobListing.overall_match_score >= min_score)
    
    if source:
        query = query.filter(JobListing.source == source)
    
    # Order by match score
    query = query.order_by(desc(JobListing.overall_match_score))
    
    # Pagination
    jobs = query.offset(offset).limit(limit).all()
    
    return [JobListingResponse.from_orm(job) for job in jobs]


@router.get("/recommended", response_model=List[JobListingResponse])
async def get_recommended_jobs(
    min_score: float = Query(0.7, ge=0.0, le=1.0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get top recommended jobs based on match score."""
    jobs = db.query(JobListing).filter(
        and_(
            JobListing.overall_match_score >= min_score,
            JobListing.is_active == True
        )
    ).order_by(
        desc(JobListing.overall_match_score)
    ).limit(limit).all()
    
    return [JobListingResponse.from_orm(job) for job in jobs]


@router.get("/{job_id}", response_model=JobListingResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific job listing by ID."""
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobListingResponse.from_orm(job)


@router.post("/{job_id}/refresh")
async def refresh_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Re-scrape and update a specific job listing."""
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Re-scrape the job using JobSourceManager
    # Note: This is a simplified refresh - full implementation would need source-specific logic
    if job.source not in SUPPORTED_SOURCES:
        raise HTTPException(status_code=400, detail=f"Source not supported: {job.source}")
    
    # For now, just return success - full refresh would require source-specific scraping
    return {"message": "Job refresh not yet implemented for this source", "job_id": job_id, "source": job.source}

