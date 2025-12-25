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
            # Filter keywords to only skill-related terms (Option B from analysis)
            # This prevents inflating job_skill_count with generic keywords
            # Reuse keywords already extracted above instead of re-extracting
            all_keywords = keywords
            
            # Pre-build set of all skill name variations for O(1) lookup
            # This optimizes filtering from O(n*m) to O(n)
            skill_name_set = set()
            for skill_name in self.skill_profile.keys():
                skill_name_lower = skill_name.lower()
                skill_name_set.add(skill_name_lower)
                # Add normalized variants for better matching
                variants = get_skill_variants(skill_name)
                skill_name_set.update(v.lower() for v in variants)
            
            # Filter to only keywords that could be skills (match against skill profile)
            # This ensures job_skill_count represents actual skills, not all keywords
            job_skill_terms = [
                kw for kw in all_keywords 
                if kw.lower() in skill_name_set or any(
                    skill_name.lower() in kw.lower() or kw.lower() in skill_name.lower()
                    for skill_name in skill_name_set
                )
            ]
            
            # If no skill-related keywords found, use conservative fallback
            # Using matched_skills count assumes we matched all required skills, which may not be true
            # Use max to ensure at least 1 if we have matches, preventing division by zero
            unique_job_skill_terms = len(set(job_skill_terms))
            if unique_job_skill_terms > 0:
                job_skill_count = unique_job_skill_terms
            elif matched_skills:
                # Fallback: assume job requires at least as many skills as we matched
                # This is conservative and prevents artificially high match ratios
                job_skill_count = max(len(matched_skills), 1)
            else:
                job_skill_count = 1  # Prevent division by zero
            
            # Match ratio: how many of our skills matched vs how many skills job requires
            # Use job_skill_count as denominator (not max) to correctly calculate coverage
            if job_skill_count > 0:
                match_ratio = min(len(matched_skills) / job_skill_count, 1.0)  # Cap at 1.0
            else:
                # No skills extracted from job - treat as perfect match if we have skills
                match_ratio = 1.0 if matched_skills else 0.0
            
            # Base score from proficiency (0-1, normalized from 1-5 scale)
            proficiency_score = avg_proficiency
            
            # Boost score based on number of matches (more matches = better)
            # Use logarithmic scaling to prevent over-weighting many matches
            # 1 match = 0.1, 3 matches = 0.3, 5 matches = 0.5, 10+ matches = 1.0
            match_count_boost = min(len(matched_skills) / 10.0, 1.0)
            
            # Formula to produce scores in 0.5-0.7+ range for good matches:
            # - proficiency_score (50%): Quality of matches - user's skill level
            # - match_ratio (30%): Primary indicator of fit - how many required skills matched
            # - match_count_boost (20%): Breadth bonus - rewards having more matching skills
            # Target: 50-70% skills matched with high proficiency → 0.5-0.7+ score
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

