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
import json
import time
from pathlib import Path

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
    # Use a debug log path in the project directory instead of hardcoded user path
    debug_log_path = Path(__file__).parent.parent.parent / "debug.log"
    
    def ensure_debug_log_dir():
        """Ensure debug log directory exists."""
        try:
            debug_log_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    
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
        # Create directory if it doesn't exist
        debug_log_path.parent.mkdir(parents=True, exist_ok=True)
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
            ensure_debug_log_dir()
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
                ensure_debug_log_dir()
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
                ensure_debug_log_dir()
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
            ensure_debug_log_dir()
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
        # #endregion agent log
        
        # Match and score jobs
        # #region agent log
        try:
            log_entry = {
                "sessionId": "debug-session",
                "runId": f"run-{int(time.time())}",
                "hypothesisId": "H6",
                "location": "jobs.py:search_jobs",
                "message": "Attempting to create SkillMatcher",
                "data": {
                    "all_jobs_count": len(all_jobs),
                    "sources_searched": sources_searched
                },
                "timestamp": int(time.time() * 1000)
            }
            debug_log_path = Path(r"d:\CodeRepositories\.cursor\debug.log")
            debug_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
        # #endregion agent log
        
        try:
            matcher = SkillMatcher(db)
            print(f"[DEBUG] SkillMatcher created successfully")  # Console output
            # #region agent log
            try:
                log_entry = {
                    "sessionId": "debug-session",
                    "runId": f"run-{int(time.time())}",
                    "hypothesisId": "H6",
                    "location": "jobs.py:search_jobs",
                    "message": "SkillMatcher created successfully - using MAIN path",
                    "data": {"path": "main"},
                    "timestamp": int(time.time() * 1000)
                }
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
            # #endregion agent log
        except Exception as e:
            logger.error(f"Error creating SkillMatcher: {e}", exc_info=True)
            print(f"[ENDPOINT ERROR] Error creating SkillMatcher: {e}")
            # #region agent log
            try:
                log_entry = {
                    "sessionId": "debug-session",
                    "runId": f"run-{int(time.time())}",
                    "hypothesisId": "H6",
                    "location": "jobs.py:search_jobs",
                    "message": "SkillMatcher creation failed - using EARLY RETURN path",
                    "data": {
                        "path": "early_return",
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
            # #endregion agent log
            # If matcher fails, return jobs without scoring
            # Set default scores to 0.0 to ensure schema compliance
            matched_jobs = []
            print(f"[DEBUG] Using EARLY RETURN path (no scoring)")  # Console output
            print(f"[DEBUG] EARLY RETURN PATH: Processing {len(all_jobs)} jobs without scoring")  # Console output
            for idx, job_data in enumerate(all_jobs):
                # Validate required fields
                source = job_data.get("source", "").strip()
                source_id = job_data.get("source_id", "").strip() if job_data.get("source_id") else None
                title = job_data.get("title", "").strip()
                company = job_data.get("company", "").strip()
                url = job_data.get("url", "").strip()
                
                # Fallback: set source from search context if missing
                if not source:
                    # Try to infer source from sources_searched (use first one as fallback)
                    if sources_searched:
                        source = sources_searched[0]
                        job_data["source"] = source
                        logger.warning(f"Job missing source field, inferred from search context: {source}")
                
                # Skip jobs with missing required fields
                if not source or not title or not company or not url:
                    logger.warning(f"Skipping job with missing required fields: source={source}, title={title}, company={company}, url={url}")
                    print(f"[DEBUG] EARLY RETURN: Job {idx+1} SKIPPED (missing fields)")  # Console output
                    continue
                
                print(f"[DEBUG] EARLY RETURN: Job {idx+1} processing '{title}' at {company}")  # Console output
                # Create job listing without scoring but with default scores
                existing = db.query(JobListing).filter(
                    JobListing.source == source,
                    JobListing.source_id == source_id if source_id else JobListing.source_id.is_(None)
                ).first()
                
                if not existing:
                    job_listing = JobListing(
                        title=title,
                        company=company,
                        location=job_data.get("location"),
                        source=source,
                        source_id=source_id,
                        url=url,
                        description=job_data.get("description"),
                        skill_match_score=0.0,
                        experience_match_score=0.0,
                        overall_match_score=0.0,
                    )
                    db.add(job_listing)
                    matched_jobs.append(job_listing)
                    print(f"[DEBUG] EARLY RETURN: Job {idx+1} ADDED (new job)")  # Console output
                else:
                    # Ensure existing job has scores set
                    if existing.skill_match_score is None:
                        existing.skill_match_score = 0.0
                    if existing.experience_match_score is None:
                        existing.experience_match_score = 0.0
                    if existing.overall_match_score is None:
                        existing.overall_match_score = 0.0
                    matched_jobs.append(existing)
                    print(f"[DEBUG] EARLY RETURN: Job {idx+1} ADDED (existing job)")  # Console output
            
            db.commit()
            print(f"[DEBUG] EARLY RETURN: {len(matched_jobs)} jobs in matched_jobs before response conversion")  # Console output
            # #region agent log
            try:
                log_entry = {
                    "sessionId": "debug-session",
                    "runId": f"run-{int(time.time())}",
                    "hypothesisId": "H6",
                    "location": "jobs.py:search_jobs",
                    "message": "Early return path - before response conversion",
                    "data": {
                        "matched_jobs_count": len(matched_jobs),
                        "all_jobs_count": len(all_jobs)
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
            # #endregion agent log
            job_responses = [JobListingResponse.from_orm(job) for job in matched_jobs]
            print(f"[DEBUG] EARLY RETURN: {len(job_responses)} jobs after response conversion")  # Console output
            return JobSearchResponse(
                jobs=job_responses,
                count=len(job_responses),
                sources_searched=sources_searched
            )
        
        matched_jobs = []
        new_jobs_count = 0
        updated_jobs_count = 0
        
        try:
            print(f"[DEBUG] Processing {len(all_jobs)} jobs from source_manager...")  # Console output
            for idx, job_data in enumerate(all_jobs):
                # Validate required fields
                source = job_data.get("source", "").strip()
                source_id = job_data.get("source_id", "").strip() if job_data.get("source_id") else None
                title = job_data.get("title", "").strip()
                company = job_data.get("company", "").strip()
                url = job_data.get("url", "").strip()
                
                # Fallback: set source from search context if missing
                if not source:
                    # Try to infer source from sources_searched (use first one as fallback)
                    if sources_searched:
                        source = sources_searched[0]
                        job_data["source"] = source
                        logger.warning(f"Job missing source field, inferred from search context: {source}")
                        print(f"[DEBUG] Job {idx+1}: Inferred source={source}")  # Console output
                
                # Skip jobs with missing required fields
                if not source or not title or not company or not url:
                    logger.warning(f"Skipping job with missing required fields: source={source}, title={title}, company={company}, url={url}")
                    print(f"[DEBUG] Job {idx+1} SKIPPED: source={bool(source)}, title={bool(title)}, company={bool(company)}, url={bool(url)}")  # Console output
                    continue
                
                print(f"[DEBUG] Job {idx+1}: Processing '{title}' at {company} (source={source})")  # Console output
                
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
                # #region agent log
                debug_log_path = Path(r"d:\CodeRepositories\.cursor\debug.log")
                try:
                    log_entry = {
                        "sessionId": "debug-session",
                        "runId": f"run-{int(time.time())}",
                        "hypothesisId": "H1",
                        "location": "jobs.py:search_jobs",
                        "message": "Before match score calculation",
                        "data": {
                            "job_idx": idx + 1,
                            "title": title,
                            "company": company,
                            "source": source,
                            "description_length": len(description),
                            "has_description": bool(description)
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    debug_log_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(debug_log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_entry) + "\n")
                except Exception:
                    pass
                # #endregion agent log
                
                try:
                    scores = matcher.calculate_match_score(description)
                    job_listing.skill_match_score = scores.get("skill_match_score", 0.0)
                    job_listing.experience_match_score = scores.get("experience_match_score", 0.0)
                    job_listing.overall_match_score = scores.get("overall_match_score", 0.0)
                    
                    # #region agent log
                    try:
                        log_entry = {
                            "sessionId": "debug-session",
                            "runId": f"run-{int(time.time())}",
                            "hypothesisId": "H2",
                            "location": "jobs.py:search_jobs",
                            "message": "After match score calculation",
                            "data": {
                                "job_idx": idx + 1,
                                "title": title,
                                "skill_match_score": job_listing.skill_match_score,
                                "experience_match_score": job_listing.experience_match_score,
                                "overall_match_score": job_listing.overall_match_score
                            },
                            "timestamp": int(time.time() * 1000)
                        }
                        with open(debug_log_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps(log_entry) + "\n")
                    except Exception:
                        pass
                    # #endregion agent log
                    
                    print(f"[DEBUG] Job {idx+1} scores: skill={job_listing.skill_match_score:.2f}, exp={job_listing.experience_match_score:.2f}, overall={job_listing.overall_match_score:.2f}")  # Console output
                except Exception as score_error:
                    logger.error(f"Error calculating match score for job {title}: {score_error}", exc_info=True)
                    # Set default scores if matching fails
                    job_listing.skill_match_score = 0.0
                    job_listing.experience_match_score = 0.0
                    job_listing.overall_match_score = 0.0
                    
                    # #region agent log
                    try:
                        log_entry = {
                            "sessionId": "debug-session",
                            "runId": f"run-{int(time.time())}",
                            "hypothesisId": "H3",
                            "location": "jobs.py:search_jobs",
                            "message": "Match score calculation failed",
                            "data": {
                                "job_idx": idx + 1,
                                "title": title,
                                "error": str(score_error),
                                "scores_set_to_zero": True
                            },
                            "timestamp": int(time.time() * 1000)
                        }
                        with open(debug_log_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps(log_entry) + "\n")
                    except Exception:
                        pass
                    # #endregion agent log
                
                # Only include if meets minimum score
                # Use default 0.0 if min_match_score is None (return all jobs by default)
                # Users can set min_match_score in request to filter by score
                min_score = request.min_match_score if request.min_match_score is not None else 0.0
                
                # #region agent log
                try:
                    log_entry = {
                        "sessionId": "debug-session",
                        "runId": f"run-{int(time.time())}",
                        "hypothesisId": "H4",
                        "location": "jobs.py:search_jobs",
                        "message": "Checking min_score threshold",
                        "data": {
                            "job_idx": idx + 1,
                            "title": title,
                            "overall_match_score": job_listing.overall_match_score,
                            "min_score": min_score,
                            "passes_threshold": job_listing.overall_match_score >= min_score
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    with open(debug_log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_entry) + "\n")
                except Exception:
                    pass
                # #endregion agent log
                
                if job_listing.overall_match_score >= min_score:
                    matched_jobs.append(job_listing)
                    print(f"[DEBUG] Job {idx+1} ADDED to matched_jobs (score {job_listing.overall_match_score:.2f} >= {min_score})")  # Console output
                else:
                    print(f"[DEBUG] Job {idx+1} FILTERED OUT (score {job_listing.overall_match_score:.2f} < {min_score})")  # Console output
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
                ensure_debug_log_dir()
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
                ensure_debug_log_dir()
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
                ensure_debug_log_dir()
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
            ensure_debug_log_dir()
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
        # #endregion agent log
        
        # Convert to response models
        # #region agent log
        try:
            log_entry = {
                "sessionId": "debug-session",
                "runId": f"run-{int(time.time())}",
                "hypothesisId": "H5",
                "location": "jobs.py:search_jobs",
                "message": "Before response model conversion",
                "data": {
                    "matched_jobs_count": len(matched_jobs),
                    "new_jobs_count": new_jobs_count,
                    "updated_jobs_count": updated_jobs_count
                },
                "timestamp": int(time.time() * 1000)
            }
            debug_log_path = Path(__file__).parent.parent.parent / "debug.log"
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
        # #endregion agent log
        
        job_responses = []
        for job in matched_jobs:
            try:
                response = JobListingResponse.from_orm(job)
                job_responses.append(response)
            except Exception as conv_error:
                logger.error(f"Error converting job to response model: {conv_error}", exc_info=True)
                # #region agent log
                try:
                    log_entry = {
                        "sessionId": "debug-session",
                        "runId": f"run-{int(time.time())}",
                        "hypothesisId": "H5",
                        "location": "jobs.py:search_jobs",
                        "message": "Response model conversion failed",
                        "data": {
                            "job_id": job.id if hasattr(job, 'id') else None,
                            "job_title": job.title if hasattr(job, 'title') else None,
                            "error": str(conv_error)
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    debug_log_path = Path(__file__).parent.parent.parent / "debug.log"
                    with open(debug_log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_entry) + "\n")
                except Exception:
                    pass
                # #endregion agent log
        
        print(f"[DEBUG] Final response: {len(job_responses)} jobs, {new_jobs_count} new, {updated_jobs_count} updated")  # Console output
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
    try:
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
        
        # Ensure all jobs have required fields set before conversion
        for job in jobs:
            if job.skill_match_score is None:
                job.skill_match_score = 0.0
            if job.experience_match_score is None:
                job.experience_match_score = 0.0
            if job.overall_match_score is None:
                job.overall_match_score = 0.0
        
        return [JobListingResponse.from_orm(job) for job in jobs]
    except Exception as e:
        logger.error(f"Error in list_jobs: {e}", exc_info=True)
        # Return empty list on error to maintain schema compliance
        return []


@router.get("/recommended", response_model=List[JobListingResponse])
async def get_recommended_jobs(
    min_score: float = Query(0.7, ge=0.0, le=1.0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get top recommended jobs based on match score."""
    try:
        # Filter jobs with score >= min_score, handling None scores
        jobs = db.query(JobListing).filter(
            and_(
                JobListing.overall_match_score.isnot(None),
                JobListing.overall_match_score >= min_score,
                JobListing.is_active == True
            )
        ).order_by(
            desc(JobListing.overall_match_score)
        ).limit(limit).all()
        
        # Ensure all jobs have required fields set before conversion
        for job in jobs:
            if job.skill_match_score is None:
                job.skill_match_score = 0.0
            if job.experience_match_score is None:
                job.experience_match_score = 0.0
            if job.overall_match_score is None:
                job.overall_match_score = 0.0
        
        return [JobListingResponse.from_orm(job) for job in jobs]
    except Exception as e:
        logger.error(f"Error in get_recommended_jobs: {e}", exc_info=True)
        # Return empty list on error to maintain schema compliance
        return []


@router.get("/{job_id}", response_model=JobListingResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific job listing by ID."""
    try:
        job = db.query(JobListing).filter(JobListing.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Ensure all required fields are set before conversion
        if job.skill_match_score is None:
            job.skill_match_score = 0.0
        if job.experience_match_score is None:
            job.experience_match_score = 0.0
        if job.overall_match_score is None:
            job.overall_match_score = 0.0
        
        return JobListingResponse.from_orm(job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


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

