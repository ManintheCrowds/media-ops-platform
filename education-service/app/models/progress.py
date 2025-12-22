"""User progress model."""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class ProgressStatus(str, enum.Enum):
    """Progress status enum."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class UserProgress(Base):
    """User progress model for tracking learning progress."""
    
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)  # Reference to platform user
    content_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False, index=True)
    status = Column(SQLEnum(ProgressStatus), default=ProgressStatus.NOT_STARTED, nullable=False)
    progress_percentage = Column(Float, default=0.0, nullable=False)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSON)  # Progress-specific data
    
    # Relationships
    content_item = relationship("ContentItem", back_populates="progress_records")




