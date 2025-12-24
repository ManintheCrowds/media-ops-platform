"""Skill profile model for user skills."""

from sqlalchemy import Column, Integer, String, Float, Index
from app.database import Base


class SkillProfile(Base):
    """User skill profile with proficiency levels."""
    
    __tablename__ = "skill_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String(100), nullable=False, unique=True, index=True)
    proficiency_level = Column(Integer, nullable=False)  # 1-5 scale
    experience_years = Column(Float, default=0.0)
    category = Column(String(50), index=True)  # 'technical', 'infrastructure', 'soft', etc.
    
    # Indexes
    __table_args__ = (
        Index('idx_category_proficiency', 'category', 'proficiency_level'),
    )

