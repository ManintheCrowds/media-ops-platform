"""Job-related schemas."""

from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime


class JobListingBase(BaseModel):
    """Base job listing schema."""
    title: str
    company: str
    location: Optional[str] = None
    source: str
    source_id: Optional[str] = None
    url: str
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    remote: bool = False


class JobListingCreate(JobListingBase):
    """Schema for creating a job listing."""
    raw_data: Optional[Dict[str, Any]] = None


class JobListingResponse(JobListingBase):
    """Schema for job listing response."""
    id: int
    skill_match_score: float
    experience_match_score: float
    overall_match_score: float
    scraped_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class JobSearchRequest(BaseModel):
    """Schema for job search request."""
    query: str
    location: Optional[str] = None
    sources: Optional[List[str]] = ["adzuna", "indeed", "linkedin", "glassdoor", "ziprecruiter"]
    min_match_score: Optional[float] = 0.0  # Default to 0.0 to return all jobs (users can filter by setting this)
    limit: Optional[int] = 25


class JobSearchResponse(BaseModel):
    """Schema for job search response."""
    jobs: List[JobListingResponse]
    count: int
    sources_searched: List[str]

