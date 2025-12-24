"""Initialize skill profile from resume data."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.skill_profile import SkillProfile

# Create tables
Base.metadata.create_all(bind=engine)

# Skill profile based on Andrew Schumacher's resume
SKILLS = [
    # Technical Skills (Proficiency 1-5)
    {"name": "Python", "proficiency": 5, "years": 3.0, "category": "technical"},
    {"name": "FastAPI", "proficiency": 5, "years": 1.5, "category": "technical"},
    {"name": "Flask", "proficiency": 4, "years": 2.0, "category": "technical"},
    {"name": "PostgreSQL", "proficiency": 5, "years": 2.5, "category": "technical"},
    {"name": "SQLAlchemy", "proficiency": 5, "years": 2.0, "category": "technical"},
    {"name": "Alembic", "proficiency": 4, "years": 1.5, "category": "technical"},
    {"name": "Redis", "proficiency": 4, "years": 1.0, "category": "technical"},
    {"name": "Docker", "proficiency": 5, "years": 2.5, "category": "technical"},
    {"name": "Proxmox", "proficiency": 4, "years": 1.5, "category": "technical"},
    {"name": "Linux", "proficiency": 5, "years": 5.0, "category": "technical"},
    {"name": "Prometheus", "proficiency": 4, "years": 1.0, "category": "technical"},
    {"name": "Grafana", "proficiency": 4, "years": 1.0, "category": "technical"},
    {"name": "AI/ML", "proficiency": 4, "years": 1.0, "category": "technical"},
    {"name": "PyTorch", "proficiency": 3, "years": 0.5, "category": "technical"},
    {"name": "Whisper", "proficiency": 4, "years": 0.5, "category": "technical"},
    {"name": "Automation", "proficiency": 5, "years": 4.0, "category": "technical"},
    
    # Infrastructure Skills
    {"name": "Networking", "proficiency": 4, "years": 3.0, "category": "infrastructure"},
    {"name": "VLAN", "proficiency": 4, "years": 2.0, "category": "infrastructure"},
    {"name": "VPN", "proficiency": 3, "years": 1.0, "category": "infrastructure"},
    {"name": "DNS", "proficiency": 4, "years": 2.0, "category": "infrastructure"},
    {"name": "DHCP", "proficiency": 4, "years": 2.0, "category": "infrastructure"},
    {"name": "PLC", "proficiency": 3, "years": 1.5, "category": "infrastructure"},
    {"name": "Modbus", "proficiency": 3, "years": 1.0, "category": "infrastructure"},
    {"name": "Crestron", "proficiency": 3, "years": 1.0, "category": "infrastructure"},
    
    # Soft Skills
    {"name": "Project Management", "proficiency": 4, "years": 3.0, "category": "soft"},
    {"name": "Training", "proficiency": 4, "years": 2.0, "category": "soft"},
    {"name": "Video Production", "proficiency": 3, "years": 2.0, "category": "soft"},
    {"name": "Communication", "proficiency": 5, "years": 5.0, "category": "soft"},
]


def init_skill_profile():
    """Initialize skill profile in database."""
    db: Session = SessionLocal()
    
    try:
        # Clear existing skills
        db.query(SkillProfile).delete()
        
        # Add skills
        for skill_data in SKILLS:
            skill = SkillProfile(
                skill_name=skill_data["name"],
                proficiency_level=skill_data["proficiency"],
                experience_years=skill_data["years"],
                category=skill_data["category"]
            )
            db.add(skill)
        
        db.commit()
        print(f"Successfully initialized {len(SKILLS)} skills in profile")
        
    except Exception as e:
        db.rollback()
        print(f"Error initializing skill profile: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_skill_profile()

