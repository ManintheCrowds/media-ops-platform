"""Tests for cover letter generation."""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.cover_letter import CoverLetterGenerator


@pytest.fixture
def generator():
    """Create a cover letter generator."""
    return CoverLetterGenerator()


@pytest.mark.asyncio
async def test_cover_letter_generation_success(generator):
    """Test successful cover letter generation."""
    job_listing = {
        "title": "Python Developer",
        "company": "Test Company",
        "description": "We need a Python developer with FastAPI experience."
    }
    
    skill_profile = {
        "matched_skills": [
            {"skill": "Python", "proficiency": 5},
            {"skill": "FastAPI", "proficiency": 5}
        ],
        "summary": {"total_skills": 20}
    }
    
    with patch('app.services.cover_letter.CoverLetterGenerator._check_ollama_available', return_value=True):
        with patch('app.services.cover_letter.CoverLetterGenerator.client.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "response": "Dear Hiring Manager,\n\nI am writing to apply..."
            }
            mock_response.raise_for_status = AsyncMock()
            mock_post.return_value = mock_response
            
            result = await generator.generate_cover_letter(job_listing, skill_profile)
            
            assert result is not None
            assert "Dear" in result or "Hiring" in result


@pytest.mark.asyncio
async def test_cover_letter_generation_ollama_unavailable(generator):
    """Test cover letter generation when Ollama is unavailable."""
    job_listing = {"title": "Test", "company": "Test", "description": "Test"}
    skill_profile = {"matched_skills": [], "summary": {}}
    
    with patch('app.services.cover_letter.CoverLetterGenerator._check_ollama_available', return_value=False):
        result = await generator.generate_cover_letter(job_listing, skill_profile)
        assert result is None


def test_build_prompt(generator):
    """Test prompt building."""
    job_listing = {
        "title": "Python Developer",
        "company": "Test Company",
        "description": "Python and FastAPI required."
    }
    
    skill_profile = {
        "matched_skills": [{"skill": "Python", "proficiency": 5}],
        "summary": {}
    }
    
    prompt = generator._build_prompt(job_listing, skill_profile, "professional", "medium")
    
    assert "Python Developer" in prompt
    assert "Test Company" in prompt
    assert "professional" in prompt.lower()

