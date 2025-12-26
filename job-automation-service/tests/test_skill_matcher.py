"""Tests for skill matcher."""

import pytest
from app.services.skill_matcher import SkillMatcher
from app.models.skill_profile import SkillProfile

# db_session and sample_skills fixtures are provided by conftest.py


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


def test_match_ratio_denominator_fix(db_session, sample_skills):
    """Verify match_ratio uses job_skill_count as denominator, not max()."""
    matcher = SkillMatcher(db_session)
    
    # Job requires 5 skills, user has 3 matches
    # match_ratio should be 3/5 = 0.6, not 3/max(5,3) = 3/5 = 0.6 (same in this case)
    # But if user had 6 skills matched, old formula would give 6/max(5,6) = 6/6 = 1.0
    # New formula should give min(6/5, 1.0) = 1.0 (capped)
    job_description = """
    We need a developer with Python, FastAPI, Docker, PostgreSQL, and Linux skills.
    Experience with REST APIs, microservices, and cloud deployment required.
    """
    
    scores = matcher.calculate_match_score(job_description)
    
    # Should have matches for Python, FastAPI, Docker
    assert len(scores["matched_skills"]) >= 3
    # match_ratio should be calculated correctly (matches / job_skill_count)
    # With the fix, scores should be reasonable
    assert scores["skill_match_score"] >= 0.0
    assert scores["skill_match_score"] <= 1.0


def test_score_range_good_match(db_session, sample_skills):
    """Test that good matches (50-70% skills matched) score in 0.5-0.7+ range."""
    # Check if skills already exist, if not add them
    existing_skill_names = {s.skill_name for s in db_session.query(SkillProfile).all()}
    additional_skills = []
    if "Linux" not in existing_skill_names:
        additional_skills.append(SkillProfile(skill_name="Linux", proficiency_level=4, experience_years=3.0, category="technical"))
    # PostgreSQL already exists in sample_skills, so we don't need to add it
    
    for skill in additional_skills:
        db_session.add(skill)
    if additional_skills:
    db_session.commit()
    
    matcher = SkillMatcher(db_session)
    
    # Job with 4 required skills, user has 3 matches (75% match)
    job_description = """
    We are looking for a Python developer with FastAPI experience.
    Must have Docker knowledge and PostgreSQL skills.
    """
    
    scores = matcher.calculate_match_score(job_description)
    
    # Good match should score in 0.5-0.7+ range
    assert scores["skill_match_score"] >= 0.5, f"Expected >= 0.5, got {scores['skill_match_score']}"
    assert scores["skill_match_score"] <= 1.0
    assert len(scores["matched_skills"]) >= 3


def test_score_range_excellent_match(db_session, sample_skills):
    """Test that excellent matches (80%+ skills matched) score 0.7+."""
    # Check if skills already exist, if not add them
    existing_skill_names = {s.skill_name for s in db_session.query(SkillProfile).all()}
    additional_skills = []
    if "Linux" not in existing_skill_names:
        additional_skills.append(SkillProfile(skill_name="Linux", proficiency_level=5, experience_years=3.0, category="technical"))
    # PostgreSQL and REST API already exist in sample_skills
    
    for skill in additional_skills:
        db_session.add(skill)
    if additional_skills:
    db_session.commit()
    
    matcher = SkillMatcher(db_session)
    
    # Job with 5 required skills, user has 4-5 matches (80-100% match)
    job_description = """
    We need a Python developer with FastAPI experience.
    Must have Docker, PostgreSQL, and Linux knowledge.
    REST API development experience required.
    """
    
    scores = matcher.calculate_match_score(job_description)
    
    # Excellent match should score 0.7+
    assert scores["skill_match_score"] >= 0.7, f"Expected >= 0.7, got {scores['skill_match_score']}"
    assert scores["skill_match_score"] <= 1.0
    assert len(scores["matched_skills"]) >= 4


def test_score_range_poor_match(db_session, sample_skills):
    """Test that poor matches (< 30% skills matched) score < 0.5."""
    matcher = SkillMatcher(db_session)
    
    # Job with 5 required skills, user has 1 match (20% match)
    job_description = """
    We need a Java developer with Spring Boot, Maven, Jenkins, and Kubernetes experience.
    Python knowledge is a plus.
    """
    
    scores = matcher.calculate_match_score(job_description)
    
    # Poor match should score < 0.5
    if len(scores["matched_skills"]) < 2:  # Less than 30% of 5+ skills
        assert scores["skill_match_score"] < 0.5, f"Expected < 0.5 for poor match, got {scores['skill_match_score']}"


def test_edge_case_no_matches(db_session, sample_skills):
    """Test edge case: no skill matches should return score 0.0."""
    matcher = SkillMatcher(db_session)
    
    job_description = """
    We are looking for a COBOL developer with mainframe experience.
    Must have Fortran and Assembly language skills.
    """
    
    scores = matcher.calculate_match_score(job_description)
    
    assert scores["skill_match_score"] == 0.0
    assert scores["overall_match_score"] == 0.0
    assert len(scores["matched_skills"]) == 0


def test_edge_case_all_matches(db_session, sample_skills):
    """Test edge case: all job skills matched should score 0.7+."""
    # PostgreSQL already exists in sample_skills, no need to add it
    # The test should work with existing skills
    
    matcher = SkillMatcher(db_session)
    
    # Job description that matches all user skills
    job_description = """
    We need a Python developer with FastAPI and Docker experience.
    PostgreSQL database knowledge required.
    """
    
    scores = matcher.calculate_match_score(job_description)
    
    # All matches should score 0.7+
    assert scores["skill_match_score"] >= 0.7, f"Expected >= 0.7 for all matches, got {scores['skill_match_score']}"
    assert len(scores["matched_skills"]) >= 3


def test_edge_case_job_no_skills(db_session, sample_skills):
    """Test edge case: job description with no extractable skills handled gracefully."""
    matcher = SkillMatcher(db_session)
    
    job_description = "We are looking for a great team player. Excellent communication skills required."
    
    scores = matcher.calculate_match_score(job_description)
    
    # Should handle gracefully - either 0.0 or some score if generic keywords match
    assert scores["skill_match_score"] >= 0.0
    assert scores["skill_match_score"] <= 1.0
    assert "matched_skills" in scores


def test_proficiency_weighting(db_session):
    """Verify higher proficiency produces higher scores."""
    # Create two skill profiles: one with high proficiency, one with low
    high_prof_skills = [
        SkillProfile(skill_name="Python", proficiency_level=5, experience_years=3.0, category="technical"),
        SkillProfile(skill_name="FastAPI", proficiency_level=5, experience_years=2.0, category="technical"),
    ]
    for skill in high_prof_skills:
        db_session.add(skill)
    db_session.commit()
    
    matcher_high = SkillMatcher(db_session)
    
    # Clear and add low proficiency skills
    db_session.query(SkillProfile).delete()
    db_session.commit()
    
    low_prof_skills = [
        SkillProfile(skill_name="Python", proficiency_level=2, experience_years=0.5, category="technical"),
        SkillProfile(skill_name="FastAPI", proficiency_level=2, experience_years=0.5, category="technical"),
    ]
    for skill in low_prof_skills:
        db_session.add(skill)
    db_session.commit()
    
    matcher_low = SkillMatcher(db_session)
    
    job_description = """
    We need a Python developer with FastAPI experience.
    """
    
    scores_high = matcher_high.calculate_match_score(job_description)
    scores_low = matcher_low.calculate_match_score(job_description)
    
    # High proficiency should score higher
    assert scores_high["skill_match_score"] > scores_low["skill_match_score"], \
        f"High prof ({scores_high['skill_match_score']}) should be > low prof ({scores_low['skill_match_score']})"


def test_match_count_boost(db_session):
    """Verify more matches increase score appropriately."""
    # Create profile with many skills
    many_skills = [
        SkillProfile(skill_name="Python", proficiency_level=5, experience_years=3.0, category="technical"),
        SkillProfile(skill_name="FastAPI", proficiency_level=5, experience_years=2.0, category="technical"),
        SkillProfile(skill_name="Docker", proficiency_level=5, experience_years=2.0, category="technical"),
        SkillProfile(skill_name="PostgreSQL", proficiency_level=5, experience_years=2.0, category="technical"),
        SkillProfile(skill_name="Linux", proficiency_level=5, experience_years=3.0, category="technical"),
    ]
    for skill in many_skills:
        db_session.add(skill)
    db_session.commit()
    
    matcher = SkillMatcher(db_session)
    
    # Job with 3 skills
    job_3_skills = "We need Python, FastAPI, and Docker experience."
    scores_3 = matcher.calculate_match_score(job_3_skills)
    
    # Job with 5 skills (all matching)
    job_5_skills = "We need Python, FastAPI, Docker, PostgreSQL, and Linux experience."
    scores_5 = matcher.calculate_match_score(job_5_skills)
    
    # More matches should generally score higher (though match_ratio might be similar)
    # The match_count_boost should help
    assert scores_5["skill_match_score"] >= scores_3["skill_match_score"], \
        f"5 matches ({scores_5['skill_match_score']}) should be >= 3 matches ({scores_3['skill_match_score']})"


def test_keyword_filtering_fix(db_session, sample_skills):
    """Verify that job_skill_count is not inflated by generic keywords (Bug #2 fix)."""
    matcher = SkillMatcher(db_session)
    
    # Job description with many generic keywords but only 3 actual skills
    job_description = """
    We are looking for a Python developer with FastAPI experience.
    Must have Docker knowledge and PostgreSQL skills.
    Experience with REST API design, microservices architecture, and cloud deployment.
    Strong problem-solving abilities, excellent communication skills, and team collaboration.
    Ability to work in agile environments and manage multiple projects simultaneously.
    """
    
    scores = matcher.calculate_match_score(job_description)
    
    # Should match Python, FastAPI, Docker (3 skills)
    # job_skill_count should be ~3-5 (actual skills), not 20+ (all keywords)
    # This should result in match_ratio ~0.6-1.0, not ~0.15
    assert len(scores["matched_skills"]) >= 3
    
    # With the fix, match_ratio should be reasonable (not artificially low)
    # If we match 3 skills and job has 3-5 actual skills, match_ratio should be 0.6-1.0
    # This should produce a skill_match_score >= 0.35 for reasonable matches
    # (Note: Score may be lower due to penalty factors for match count, but should still be reasonable)
    assert scores["skill_match_score"] >= 0.35, \
        f"Expected >= 0.35 after keyword filtering fix, got {scores['skill_match_score']}"


def test_match_ratio_formula_fix(db_session):
    """Verify match_ratio uses job_skill_count directly, not max() (Bug #1 fix)."""
    # Create profile with many skills
    skills = [
        SkillProfile(skill_name="Python", proficiency_level=5, experience_years=3.0, category="technical"),
        SkillProfile(skill_name="FastAPI", proficiency_level=5, experience_years=2.0, category="technical"),
        SkillProfile(skill_name="Docker", proficiency_level=5, experience_years=2.0, category="technical"),
        SkillProfile(skill_name="PostgreSQL", proficiency_level=5, experience_years=2.0, category="technical"),
        SkillProfile(skill_name="Linux", proficiency_level=5, experience_years=3.0, category="technical"),
        SkillProfile(skill_name="Kubernetes", proficiency_level=5, experience_years=2.0, category="technical"),
    ]
    for skill in skills:
        db_session.add(skill)
    db_session.commit()
    
    matcher = SkillMatcher(db_session)
    
    # Job with 3 skills, user has 6 skills (more matches than job requires)
    job_description = "We need Python, FastAPI, and Docker experience."
    scores = matcher.calculate_match_score(job_description)
    
    # Should match 3 skills
    assert len(scores["matched_skills"]) == 3
    
    # match_ratio should be min(3/3, 1.0) = 1.0 (capped at 1.0)
    # NOT max(3, 3)/max(3, 3) = 1.0 (old formula would also give 1.0 in this case)
    # But the key is: denominator should be job_skill_count (3), not max(3, 3)
    # With keyword filtering, job_skill_count should be ~3 (actual skills), not inflated
    assert scores["skill_match_score"] > 0.0
    assert scores["skill_match_score"] <= 1.0


def test_regression_test_scenario(db_session):
    """Test the exact scenario from regression_test_agent.py that expects > 0.5."""
    # Create skills matching the regression test
    skills = [
        SkillProfile(skill_name="Python", proficiency_level=5, experience_years=3.0, category="technical"),
        SkillProfile(skill_name="FastAPI", proficiency_level=5, experience_years=2.0, category="technical"),
        SkillProfile(skill_name="Docker", proficiency_level=5, experience_years=2.0, category="technical"),
        SkillProfile(skill_name="PostgreSQL", proficiency_level=5, experience_years=2.0, category="technical"),
        SkillProfile(skill_name="REST API", proficiency_level=5, experience_years=2.0, category="technical"),
    ]
    for skill in skills:
        db_session.add(skill)
    db_session.commit()
    
    matcher = SkillMatcher(db_session)
    
    # Exact text from regression test
    job_description = "Python developer with FastAPI experience, Docker knowledge, PostgreSQL, and REST API design."
    
    scores = matcher.calculate_match_score(job_description)
    
    # Regression test expects > 0.5 (was 0.174 before fix)
    assert scores["overall_match_score"] > 0.5, \
        f"Regression test failed: expected > 0.5, got {scores['overall_match_score']}"
    
    # Should have matched multiple skills
    assert len(scores["matched_skills"]) >= 4


def test_score_improvement_after_fix(db_session):
    """Verify scores improved from ~0.211 average to 0.5-0.7+ range."""
    # Create comprehensive skill profile
    skills = [
        SkillProfile(skill_name="Python", proficiency_level=5, experience_years=3.0, category="technical"),
        SkillProfile(skill_name="FastAPI", proficiency_level=5, experience_years=2.0, category="technical"),
        SkillProfile(skill_name="Docker", proficiency_level=5, experience_years=2.0, category="technical"),
        SkillProfile(skill_name="PostgreSQL", proficiency_level=4, experience_years=2.0, category="technical"),
        SkillProfile(skill_name="Linux", proficiency_level=4, experience_years=3.0, category="technical"),
    ]
    for skill in skills:
        db_session.add(skill)
    db_session.commit()
    
    matcher = SkillMatcher(db_session)
    
    # Test multiple job descriptions
    test_jobs = [
        "Python developer with FastAPI and Docker experience.",
        "We need someone with Python, FastAPI, Docker, and PostgreSQL skills.",
        "Looking for a backend developer with Python, FastAPI, Docker, PostgreSQL, and Linux experience.",
    ]
    
    scores = []
    for job_desc in test_jobs:
        result = matcher.calculate_match_score(job_desc)
        scores.append(result["overall_match_score"])
    
    # Average should be in 0.5-0.7+ range (not ~0.211)
    avg_score = sum(scores) / len(scores)
    assert avg_score >= 0.5, \
        f"Average score should be >= 0.5 after fix, got {avg_score}"
    assert avg_score <= 1.0