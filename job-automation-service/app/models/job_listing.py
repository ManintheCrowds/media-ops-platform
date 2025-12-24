"""Job listing model."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class JobListing(Base):
    """Job listing from various sources."""
    
    __tablename__ = "job_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), index=True)
    source = Column(String(50), nullable=False, index=True)  # 'indeed', 'linkedin', 'glassdoor', 'ziprecruiter'
    source_id = Column(String(255), unique=True)  # External ID from source
    url = Column(Text, nullable=False)
    description = Column(Text)
    requirements = Column(Text)
    salary_range = Column(String(100))
    job_type = Column(String(50))  # 'full-time', 'contract', 'part-time', etc.
    remote = Column(Boolean, default=False)
    
    # Matching scores
    skill_match_score = Column(Float, default=0.0, index=True)
    experience_match_score = Column(Float, default=0.0)
    overall_match_score = Column(Float, default=0.0, index=True)
    
    # Metadata
    raw_data = Column(JSON)  # Store full API response or scraped HTML
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    applications = relationship("Application", back_populates="job_listing", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_source_source_id', 'source', 'source_id'),
        Index('idx_overall_match_active', 'overall_match_score', 'is_active'),
    )

