"""Application-related schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ApplicationBase(BaseModel):
    """Base application schema."""
    job_listing_id: int
    status: str = "pending"
    notes: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    """Schema for creating an application."""
    cover_letter: Optional[str] = None


class ApplicationUpdate(BaseModel):
    """Schema for updating an application."""
    status: Optional[str] = None
    notes: Optional[str] = None
    cover_letter: Optional[str] = None
    next_followup: Optional[datetime] = None


class ApplicationResponse(ApplicationBase):
    """Schema for application response."""
    id: int
    applied_at: Optional[datetime] = None
    cover_letter: Optional[str] = None
    last_followup: Optional[datetime] = None
    next_followup: Optional[datetime] = None
    followup_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    job_listing: Optional[dict] = None  # Will include job listing details
    
    class Config:
        from_attributes = True


class FollowupRequest(BaseModel):
    """Schema for scheduling a follow-up."""
    days: int = 7  # Days from now
    notes: Optional[str] = None

