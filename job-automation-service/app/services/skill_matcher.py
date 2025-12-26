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
        matched_original_names = set()  # Track original skill names to prevent duplicates
        
        for skill_name, skill_data in self.skill_profile.items():
            original_name = skill_data['original_name']
            
            # Skip if we've already matched this original skill
            if original_name in matched_original_names:
                continue
            
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
                    'skill': original_name,
                    'proficiency': proficiency,
                    'category': skill_data['category']
                })
                matched_original_names.add(original_name)
                # Weight by proficiency (1-5 scale)
                skill_scores.append(proficiency / 5.0)
        
        # Calculate skill match score
        if skill_scores and matched_skills:
            # Average proficiency of matched skills (weighted)
            avg_proficiency = sum(skill_scores) / len(skill_scores)
            
            # Calculate match ratio: matched skills vs total unique skills mentioned in job
            # We need to count ALL skill-like terms in the job, not just ones in user's profile,
            # to properly calculate match ratio for poor matches.
            
            # First, extract all potential skill terms from job description
            # Look for common tech stack patterns: "Java developer", "Spring Boot", "Maven", etc.
            # These are typically capitalized or appear in specific contexts
            all_keywords = keywords
            
            # Count all distinct skill-like terms (before filtering to user's profile)
            # This gives us the true number of skills the job requires
            # Filter out common stop words and generic terms
            skill_like_terms = [
                kw for kw in all_keywords 
                if len(kw) >= 3 and kw.lower() not in {
                    'the', 'and', 'or', 'with', 'for', 'are', 'is', 'a', 'an',
                    'we', 'need', 'looking', 'developer', 'experience', 'knowledge',
                    'skills', 'required', 'must', 'have', 'plus', 'knowledge'
                }
            ]
            total_job_skills_mentioned = len(set(skill_like_terms))
            
            # Also filter to only keywords that match known skills (for match ratio calculation)
            # Pre-build set of all skill name variations for O(1) lookup
            skill_name_set = set()
            for skill_name in self.skill_profile.keys():
                skill_name_lower = skill_name.lower()
                skill_name_set.add(skill_name_lower)
                # Add normalized variants for better matching
                variants = get_skill_variants(skill_name)
                skill_name_set.update(v.lower() for v in variants)
            
            # Filter to only keywords that match known skills
            job_skill_terms = [
                kw for kw in all_keywords 
                if kw.lower() in skill_name_set or any(
                    skill_name.lower() in kw.lower() or kw.lower() in skill_name.lower()
                    for skill_name in skill_name_set
                )
            ]
            
            # Use the larger of: (1) total skills mentioned, (2) filtered terms matching user's skills
            # This ensures we don't underestimate job requirements for poor matches
            unique_job_skill_terms = len(set(job_skill_terms))
            job_skill_count = max(total_job_skills_mentioned, unique_job_skill_terms, len(matched_skills), 1)
            
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
            # More appropriate scaling for typical jobs (3-5 skills)
            # 1 match = 0.2, 3 matches = 0.6, 5 matches = 1.0
            match_count_boost = min(len(matched_skills) / 5.0, 1.0)
            
            # Formula to produce scores in 0.5-0.7+ range for good matches:
            # - match_ratio (45%): Primary indicator of fit - how many required skills matched
            # - proficiency_score (35%): Quality of matches - user's skill level
            # - match_count_boost (20%): Breadth bonus - rewards having more matching skills
            # Target: 50-70% skills matched with high proficiency → 0.5-0.7+ score
            base_score = (
                match_ratio * 0.45 +
                proficiency_score * 0.35 +
                match_count_boost * 0.20
            )
            
            # Penalize poor matches: if match count is very low, significantly reduce the score.
            # This prevents high scores for jobs where user only matches 1-2 skills out of many required.
            # The penalty is based on absolute match count, not just relative to job_skill_count,
            # because job_skill_count may be underestimated due to keyword filtering.
            # Penalty factor: 1 match = 0.25x, 2 matches = 0.5x, 3+ matches = 1.0x
            # Also apply additional penalty if match ratio is very low (< 30%)
            if len(matched_skills) == 1:
                # Very poor match: only 1 skill matched
                # Apply heavy penalty unless job_skill_count is also 1 (perfect match scenario)
                if job_skill_count == 1:
                    penalty_factor = 1.0  # Perfect match: 1 skill required, 1 matched
                else:
                    penalty_factor = 0.25  # Very poor: only 1 skill matched out of multiple required
            elif len(matched_skills) == 2:
                # Poor match: only 2 skills matched
                # Apply moderate penalty unless match ratio is good
                if match_ratio >= 0.5:
                    penalty_factor = 1.0  # Good match ratio: 2 skills matched, job only needs 2-4
                else:
                    penalty_factor = 0.5  # Poor match ratio: 2 skills matched but job needs more
            elif match_ratio < 0.3:
                # Less than 30% of required skills matched (even with 3+ matches)
                penalty_factor = 0.6
            else:
                # Good match: 3+ matches with 30%+ match ratio
                penalty_factor = 1.0
            
            skill_match_score = base_score * penalty_factor
            
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

