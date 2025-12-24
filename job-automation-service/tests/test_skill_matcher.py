"""Tests for skill matcher."""

import pytest
from app.services.skill_matcher import SkillMatcher
from app.database import SessionLocal
from app.models.skill_profile import SkillProfile


@pytest.fixture
def db_session():
    """Create a test database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_skills(db_session):
    """Create sample skills for testing."""
    skills = [
        SkillProfile(skill_name="Python", proficiency_level=5, experience_years=3.0, category="technical"),
        SkillProfile(skill_name="FastAPI", proficiency_level=5, experience_years=1.5, category="technical"),
        SkillProfile(skill_name="Docker", proficiency_level=5, experience_years=2.5, category="technical"),
    ]
    for skill in skills:
        db_session.add(skill)
    db_session.commit()
    return skills


def test_skill_matcher_initialization(db_session, sample_skills):
    """Test skill matcher initialization."""
    matcher = SkillMatcher(db_session)
    assert matcher.skill_profile is not None
    assert len(matcher.skill_profile) > 0


def test_calculate_match_score_high_match(db_session, sample_skills):
    """Test match score calculation for high match."""
    matcher = SkillMatcher(db_session)
    
    job_description = """
    We are looking for a Python developer with FastAPI experience.
    Must have Docker knowledge and PostgreSQL skills.
    """
    
    scores = matcher.calculate_match_score(job_description)
    
    assert scores["overall_match_score"] > 0.5
    assert scores["skill_match_score"] > 0.0
    assert len(scores["matched_skills"]) > 0


def test_calculate_match_score_low_match(db_session, sample_skills):
    """Test match score calculation for low match."""
    matcher = SkillMatcher(db_session)
    
    job_description = """
    We are looking for a Java developer with Spring Boot experience.
    Must have Maven and Jenkins knowledge.
    """
    
    scores = matcher.calculate_match_score(job_description)
    
    assert scores["overall_match_score"] < 0.5
    assert len(scores["matched_skills"]) == 0


def test_get_skill_profile_summary(db_session, sample_skills):
    """Test skill profile summary."""
    matcher = SkillMatcher(db_session)
    summary = matcher.get_skill_profile_summary()
    
    assert "total_skills" in summary
    assert "categories" in summary
    assert summary["total_skills"] > 0

