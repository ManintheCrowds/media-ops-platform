"""Skills matching service."""

import logging
from typing import Dict, List, Set
from sqlalchemy.orm import Session
from app.models.skill_profile import SkillProfile
from app.utils.text_processing import (
    normalize_skill_name,
    get_skill_variants,
    extract_keywords,
    extract_requirements,
    extract_experience_level
)

logger = logging.getLogger(__name__)


class SkillMatcher:
    """Match job requirements to user skills."""
    
    def __init__(self, db: Session):
        """Initialize skill matcher.
        
        Args:
            db: Database session
        """
        self.db = db
        self.skill_profile = self._load_skill_profile()
    
    def _load_skill_profile(self) -> Dict[str, Dict]:
        """Load skill profile from database.
        
        Returns:
            Dictionary mapping skill names to profile data
        """
        skills = self.db.query(SkillProfile).all()
        profile = {}
        
        for skill in skills:
            normalized = normalize_skill_name(skill.skill_name)
            profile[normalized] = {
                'proficiency': skill.proficiency_level,
                'experience_years': skill.experience_years,
                'category': skill.category,
                'original_name': skill.skill_name,
            }
            
            # Add variants
            variants = get_skill_variants(skill.skill_name)
            for variant in variants:
                if variant not in profile:
                    profile[variant] = profile[normalized]
        
        return profile
    
    def calculate_match_score(self, job_description: str) -> Dict[str, float]:
        """Calculate match scores for a job.
        
        Args:
            job_description: Job description text
        
        Returns:
            Dictionary with match scores and matched skills
        """
        if not job_description:
            return {
                'skill_match_score': 0.0,
                'experience_match_score': 0.0,
                'overall_match_score': 0.0,
                'matched_skills': []
            }
        
        description_lower = job_description.lower()
        
        # Extract keywords
        keywords = extract_keywords(job_description)
        keyword_set = set(keywords)
        
        # Match skills
        matched_skills = []
        skill_scores = []
        
        for skill_name, skill_data in self.skill_profile.items():
            variants = get_skill_variants(skill_name)
            
            # Check if any variant appears in description
            found = False
            for variant in variants:
                if variant in description_lower or variant in keyword_set:
                    found = True
                    break
            
            if found:
                proficiency = skill_data['proficiency']
                matched_skills.append({
                    'skill': skill_data['original_name'],
                    'proficiency': proficiency,
                    'category': skill_data['category']
                })
                # Weight by proficiency (1-5 scale)
                skill_scores.append(proficiency / 5.0)
        
        # Calculate skill match score
        if skill_scores and matched_skills:
            # Average proficiency of matched skills (weighted)
            avg_proficiency = sum(skill_scores) / len(skill_scores)
            
            # Calculate match ratio: matched skills vs total unique skills mentioned in job
            # Extract all skill-like terms from job description
            job_skill_terms = extract_keywords(job_description)
            job_skill_count = len(set(job_skill_terms))
            
            # Match ratio: how many of our skills matched vs how many skills job requires
            if job_skill_count > 0:
                match_ratio = len(matched_skills) / max(job_skill_count, len(matched_skills))
            else:
                match_ratio = 1.0 if matched_skills else 0.0
            
            # Base score from proficiency (0-1)
            proficiency_score = avg_proficiency
            
            # Boost score based on number of matches (more matches = better)
            match_count_boost = min(len(matched_skills) / 10.0, 1.0)  # Cap at 10 skills
            
            # Combine: proficiency (50%) + match ratio (30%) + match count boost (20%)
            skill_match_score = (
                proficiency_score * 0.5 +
                match_ratio * 0.3 +
                match_count_boost * 0.2
            )
            
            # Ensure score is in 0-1 range
            skill_match_score = min(max(skill_match_score, 0.0), 1.0)
        else:
            skill_match_score = 0.0
        
        # Calculate experience match score
        experience_keywords = [
            'python', 'fastapi', 'flask', 'api', 'automation', 'docker',
            'postgresql', 'sql', 'linux', 'infrastructure', 'devops',
            'monitoring', 'prometheus', 'grafana', 'networking', 'vlan'
        ]
        
        experience_matches = sum(
            1 for kw in experience_keywords
            if kw in description_lower
        )
        experience_match_score = min(experience_matches / max(len(experience_keywords), 1), 1.0)
        
        # Overall score (weighted: 70% skills, 30% experience)
        # Increased skill weight since that's the primary matching factor
        overall_score = (skill_match_score * 0.7) + (experience_match_score * 0.3)
        
        return {
            'skill_match_score': round(skill_match_score, 3),
            'experience_match_score': round(experience_match_score, 3),
            'overall_match_score': round(overall_score, 3),
            'matched_skills': matched_skills
        }
    
    def get_skill_profile_summary(self) -> Dict:
        """Get summary of skill profile.
        
        Returns:
            Dictionary with skill profile statistics
        """
        total_skills = len(self.skill_profile)
        categories = {}
        
        for skill_data in self.skill_profile.values():
            category = skill_data.get('category', 'other')
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        return {
            'total_skills': total_skills,
            'categories': categories,
            'avg_proficiency': sum(
                s['proficiency'] for s in self.skill_profile.values()
            ) / total_skills if total_skills > 0 else 0
        }

