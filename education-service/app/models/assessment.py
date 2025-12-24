"""Assessment models."""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class AssessmentType(str, enum.Enum):
    """Assessment type enum."""
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    PROJECT = "project"


class SubmissionStatus(str, enum.Enum):
    """Submission status enum."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    GRADED = "graded"


class Assessment(Base):
    """Assessment model for quizzes and assignments."""
    
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    content_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False, index=True)
    assessment_type = Column(SQLEnum(AssessmentType), nullable=False)
    questions = Column(JSON)  # Question data
    grading_rubric = Column(JSON)  # Grading rubric
    settings = Column(JSON)  # Time limits, attempts, etc.
    created_by = Column(String(255), nullable=False)  # Reference to platform user
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    content_item = relationship("ContentItem", back_populates="assessments")
    submissions = relationship("AssessmentSubmission", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentSubmission(Base):
    """Assessment submission model."""
    
    __tablename__ = "assessment_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)  # Reference to platform user
    answers = Column(JSON)  # User answers
    score = Column(Float, nullable=True)
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.DRAFT, nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    graded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="submissions")







