"""Skills matching API endpoints."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from app.database import get_db
from app.models.job_listing import JobListing
from app.services.skill_matcher import SkillMatcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/matching", tags=["matching"])


class ScoreRequest(BaseModel):
    """Request schema for scoring a job."""
    job_description: str


class ScoreResponse(BaseModel):
    """Response schema for job scoring."""
    skill_match_score: float
    experience_match_score: float
    overall_match_score: float
    matched_skills: List[dict]


class BatchScoreRequest(BaseModel):
    """Request schema for batch scoring."""
    job_descriptions: List[str]


class BatchScoreResponse(BaseModel):
    """Response schema for batch scoring."""
    scores: List[ScoreResponse]


class MatchingStatsResponse(BaseModel):
    """Response schema for matching statistics."""
    total_jobs: int
    average_match_score: float
    high_match_jobs: int  # > 0.7
    medium_match_jobs: int  # 0.5-0.7
    low_match_jobs: int  # < 0.5
    top_matched_skills: List[dict]
    skill_profile_summary: dict


@router.post("/score", response_model=ScoreResponse)
async def score_job(
    request: ScoreRequest,
    db: Session = Depends(get_db)
):
    """Score a job description against skill profile."""
    try:
        matcher = SkillMatcher(db)
        scores = matcher.calculate_match_score(request.job_description)
        
        # Ensure all required fields are present with defaults
        return ScoreResponse(
            skill_match_score=scores.get("skill_match_score", 0.0),
            experience_match_score=scores.get("experience_match_score", 0.0),
            overall_match_score=scores.get("overall_match_score", 0.0),
            matched_skills=scores.get("matched_skills", [])
        )
    except Exception as e:
        logger.error(f"Error calculating match score: {e}", exc_info=True)
        # Return default scores on error to maintain schema compliance
        return ScoreResponse(
            skill_match_score=0.0,
            experience_match_score=0.0,
            overall_match_score=0.0,
            matched_skills=[]
        )


@router.post("/batch-score", response_model=BatchScoreResponse)
async def batch_score_jobs(
    request: BatchScoreRequest,
    db: Session = Depends(get_db)
):
    """Score multiple job descriptions."""
    try:
        matcher = SkillMatcher(db)
        scores = []
        
        for description in request.job_descriptions:
            try:
                result = matcher.calculate_match_score(description)
                scores.append(ScoreResponse(
                    skill_match_score=result.get("skill_match_score", 0.0),
                    experience_match_score=result.get("experience_match_score", 0.0),
                    overall_match_score=result.get("overall_match_score", 0.0),
                    matched_skills=result.get("matched_skills", [])
                ))
            except Exception as e:
                logger.error(f"Error calculating match score for description: {e}", exc_info=True)
                # Add default score for failed item to maintain response structure
                scores.append(ScoreResponse(
                    skill_match_score=0.0,
                    experience_match_score=0.0,
                    overall_match_score=0.0,
                    matched_skills=[]
                ))
        
        return BatchScoreResponse(scores=scores)
    except Exception as e:
        logger.error(f"Error in batch_score_jobs: {e}", exc_info=True)
        # Return empty scores list on error
        return BatchScoreResponse(scores=[])


@router.get("/stats", response_model=MatchingStatsResponse)
async def get_matching_stats(
    db: Session = Depends(get_db)
):
    """Get matching statistics across all jobs."""
    try:
        # Get all active jobs
        jobs = db.query(JobListing).filter(JobListing.is_active == True).all()
        
        if not jobs:
            return MatchingStatsResponse(
                total_jobs=0,
                average_match_score=0.0,
                high_match_jobs=0,
                medium_match_jobs=0,
                low_match_jobs=0,
                top_matched_skills=[],
                skill_profile_summary={}
            )
        
        # Calculate statistics with safe defaults for None scores
        total_jobs = len(jobs)
        scores = [job.overall_match_score or 0.0 for job in jobs]
        avg_score = sum(scores) / total_jobs if total_jobs > 0 else 0.0
        
        high_match = sum(1 for job in jobs if (job.overall_match_score or 0.0) > 0.7)
        medium_match = sum(1 for job in jobs if 0.5 <= (job.overall_match_score or 0.0) <= 0.7)
        low_match = sum(1 for job in jobs if (job.overall_match_score or 0.0) < 0.5)
        
        # Get top matched skills (this would require tracking which skills matched)
        # For now, return empty list
        top_matched_skills = []
        
        # Get skill profile summary
        try:
            matcher = SkillMatcher(db)
            skill_profile_summary = matcher.get_skill_profile_summary()
        except Exception as e:
            logger.error(f"Error getting skill profile summary: {e}", exc_info=True)
            skill_profile_summary = {}
        
        return MatchingStatsResponse(
            total_jobs=total_jobs,
            average_match_score=round(avg_score, 3),
            high_match_jobs=high_match,
            medium_match_jobs=medium_match,
            low_match_jobs=low_match,
            top_matched_skills=top_matched_skills,
            skill_profile_summary=skill_profile_summary
        )
    except Exception as e:
        logger.error(f"Error in get_matching_stats: {e}", exc_info=True)
        # Return default stats on error
        return MatchingStatsResponse(
            total_jobs=0,
            average_match_score=0.0,
            high_match_jobs=0,
            medium_match_jobs=0,
            low_match_jobs=0,
            top_matched_skills=[],
            skill_profile_summary={}
        )

