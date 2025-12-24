"""Application tracking model."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Application(Base):
    """Track job applications."""
    
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    job_listing_id = Column(Integer, ForeignKey("job_listings.id"), nullable=False, index=True)
    
    status = Column(String(50), default="pending", index=True)  # pending, submitted, interview, rejected, offer, withdrawn
    applied_at = Column(DateTime(timezone=True))
    cover_letter = Column(Text)
    notes = Column(Text)
    
    # Follow-up tracking
    last_followup = Column(DateTime(timezone=True))
    next_followup = Column(DateTime(timezone=True), index=True)
    followup_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    job_listing = relationship("JobListing", back_populates="applications")
    
    # Indexes
    __table_args__ = (
        Index('idx_status_created', 'status', 'created_at'),
    )

