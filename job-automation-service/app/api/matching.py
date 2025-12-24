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
    matcher = SkillMatcher(db)
    scores = matcher.calculate_match_score(request.job_description)
    
    return ScoreResponse(
        skill_match_score=scores["skill_match_score"],
        experience_match_score=scores["experience_match_score"],
        overall_match_score=scores["overall_match_score"],
        matched_skills=scores["matched_skills"]
    )


@router.post("/batch-score", response_model=BatchScoreResponse)
async def batch_score_jobs(
    request: BatchScoreRequest,
    db: Session = Depends(get_db)
):
    """Score multiple job descriptions."""
    matcher = SkillMatcher(db)
    scores = []
    
    for description in request.job_descriptions:
        result = matcher.calculate_match_score(description)
        scores.append(ScoreResponse(
            skill_match_score=result["skill_match_score"],
            experience_match_score=result["experience_match_score"],
            overall_match_score=result["overall_match_score"],
            matched_skills=result["matched_skills"]
        ))
    
    return BatchScoreResponse(scores=scores)


@router.get("/stats", response_model=MatchingStatsResponse)
async def get_matching_stats(
    db: Session = Depends(get_db)
):
    """Get matching statistics across all jobs."""
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
    
    # Calculate statistics
    total_jobs = len(jobs)
    avg_score = sum(job.overall_match_score for job in jobs) / total_jobs
    
    high_match = sum(1 for job in jobs if job.overall_match_score > 0.7)
    medium_match = sum(1 for job in jobs if 0.5 <= job.overall_match_score <= 0.7)
    low_match = sum(1 for job in jobs if job.overall_match_score < 0.5)
    
    # Get top matched skills (this would require tracking which skills matched)
    # For now, return empty list
    top_matched_skills = []
    
    # Get skill profile summary
    matcher = SkillMatcher(db)
    skill_profile_summary = matcher.get_skill_profile_summary()
    
    return MatchingStatsResponse(
        total_jobs=total_jobs,
        average_match_score=round(avg_score, 3),
        high_match_jobs=high_match,
        medium_match_jobs=medium_match,
        low_match_jobs=low_match,
        top_matched_skills=top_matched_skills,
        skill_profile_summary=skill_profile_summary
    )

