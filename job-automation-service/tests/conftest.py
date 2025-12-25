"""Pytest configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.skill_profile import SkillProfile


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session using SQLite in-memory database."""
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def sample_skills(db_session):
    """Create sample skills for testing."""
    skills = [
        SkillProfile(skill_name="Python", proficiency_level=5, experience_years=3.0, category="technical"),
        SkillProfile(skill_name="FastAPI", proficiency_level=5, experience_years=1.5, category="technical"),
        SkillProfile(skill_name="Docker", proficiency_level=5, experience_years=2.5, category="technical"),
        SkillProfile(skill_name="PostgreSQL", proficiency_level=4, experience_years=2.0, category="technical"),
        SkillProfile(skill_name="REST API", proficiency_level=5, experience_years=3.0, category="technical"),
    ]
    for skill in skills:
        db_session.add(skill)
    db_session.commit()
    return skills


