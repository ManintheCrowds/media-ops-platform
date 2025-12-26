"""Cover letter generation using local LLM (Ollama)."""

import logging
import httpx
from typing import Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class CoverLetterGenerator:
    """Generate personalized cover letters using Ollama."""
    
    def __init__(self):
        """Initialize cover letter generator."""
        self.ollama_url = settings.ollama_url
        self.model = settings.ollama_model
        self.client = httpx.AsyncClient(timeout=120.0)  # Longer timeout for LLM
    
    async def generate_cover_letter(
        self,
        job_listing: Dict,
        skill_profile: Dict,
        tone: str = "professional",
        length: str = "medium"
    ) -> Optional[str]:
        """Generate a personalized cover letter.
        
        Args:
            job_listing: Job listing dictionary with title, company, description
            skill_profile: Skill profile summary
            tone: Letter tone (professional, friendly, formal)
            length: Letter length (short, medium, long)
        
        Returns:
            Generated cover letter text or None if generation failed
        """
        try:
            # Check if Ollama is available
            ollama_available = await self._check_ollama_available()
            
            if ollama_available:
                # Build prompt
                prompt = self._build_prompt(job_listing, skill_profile, tone, length)
                
                # Generate via Ollama API
                try:
                    response = await self.client.post(
                        f"{self.ollama_url}/api/generate",
                        json={
                            "model": self.model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.7,
                                "top_p": 0.9,
                            }
                        }
                    )
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    cover_letter = result.get("response", "").strip()
                    
                    if cover_letter and len(cover_letter) > 100:
                        return cover_letter
                    else:
                        logger.warning("Ollama returned empty or too short response, using fallback")
                except httpx.RequestError as e:
                    logger.warning(f"Error connecting to Ollama: {e}, using fallback")
                except httpx.HTTPStatusError as e:
                    logger.warning(f"Ollama API error: {e.response.status_code}, using fallback")
                except Exception as e:
                    logger.warning(f"Unexpected error with Ollama: {e}, using fallback")
            else:
                logger.info("Ollama service is not available, using fallback template")
            
            # Fallback: Generate template-based cover letter
            return self._generate_fallback_letter(job_listing, skill_profile, tone, length)
            
        except Exception as e:
            logger.error(f"Unexpected error generating cover letter: {e}")
            # Last resort: return basic fallback
            try:
                return self._generate_fallback_letter(job_listing, skill_profile, tone, length)
            except Exception as fallback_error:
                logger.error(f"Fallback generation also failed: {fallback_error}")
                return None
    
    def _build_prompt(
        self,
        job_listing: Dict,
        skill_profile: Dict,
        tone: str,
        length: str
    ) -> str:
        """Build prompt for cover letter generation.
        
        Args:
            job_listing: Job listing data
            skill_profile: Skill profile data
            tone: Desired tone
            length: Desired length
        
        Returns:
            Prompt string
        """
        job_title = job_listing.get("title", "the position")
        company = job_listing.get("company", "the company")
        description = job_listing.get("description", "")[:500]  # First 500 chars
        
        # Extract key requirements
        key_requirements = self._extract_key_requirements(description)
        
        # Get relevant skills
        matched_skills = skill_profile.get("matched_skills", [])
        top_skills = [
            s["skill"] for s in sorted(
                matched_skills,
                key=lambda x: x.get("proficiency", 0),
                reverse=True
            )[:5]
        ]
        
        length_instruction = {
            "short": "Keep it concise, around 200-250 words.",
            "medium": "Make it moderate length, around 300-400 words.",
            "long": "Make it comprehensive, around 500-600 words."
        }.get(length, "Make it moderate length, around 300-400 words.")
        
        tone_instruction = {
            "professional": "Use a professional and confident tone.",
            "friendly": "Use a friendly and approachable tone.",
            "formal": "Use a formal and respectful tone."
        }.get(tone, "Use a professional tone.")
        
        prompt = f"""Write a personalized cover letter for the following job application.

Position: {job_title}
Company: {company}

Job Description (excerpt):
{description}

Key Requirements:
{key_requirements}

My Relevant Skills:
{', '.join(top_skills) if top_skills else 'Python, FastAPI, Docker, PostgreSQL, Automation, Linux'}

Instructions:
- Address the letter professionally
- Highlight relevant experience and skills
- Show enthusiasm for the role
- Be specific about how my skills match the requirements
- {tone_instruction}
- {length_instruction}
- Do not include placeholders like [Your Name] or [Date] - write as if it's ready to send
- Start with "Dear Hiring Manager," and end with "Sincerely," followed by a blank line for signature

Write the complete cover letter now:"""
        
        return prompt
    
    def _extract_key_requirements(self, description: str) -> str:
        """Extract key requirements from job description.
        
        Args:
            description: Job description text
        
        Returns:
            Formatted requirements string
        """
        if not description:
            return "Not specified"
        
        # Look for common requirement patterns
        requirements = []
        
        # Technical skills mentioned
        tech_keywords = [
            "python", "fastapi", "flask", "docker", "postgresql", "sql",
            "linux", "automation", "api", "rest", "microservices",
            "kubernetes", "aws", "azure", "gcp", "ci/cd", "devops"
        ]
        
        found_tech = [
            kw for kw in tech_keywords
            if kw in description.lower()
        ]
        
        if found_tech:
            requirements.append(f"Technical: {', '.join(found_tech[:5])}")
        
        # Experience level
        if "years" in description.lower():
            import re
            years_match = re.search(r'(\d+)[\+-]?\s*years?', description.lower())
            if years_match:
                requirements.append(f"Experience: {years_match.group(1)}+ years")
        
        return "\n".join(requirements) if requirements else "See job description"
    
    async def _check_ollama_available(self) -> bool:
        """Check if Ollama service is available.
        
        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            response = await self.client.get(f"{self.ollama_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
    
    def _generate_fallback_letter(
        self,
        job_listing: Dict,
        skill_profile: Dict,
        tone: str,
        length: str
    ) -> str:
        """Generate a fallback cover letter using template when Ollama is unavailable.
        
        Args:
            job_listing: Job listing data
            skill_profile: Skill profile data
            tone: Desired tone
            length: Desired length
        
        Returns:
            Generated cover letter text
        """
        job_title = job_listing.get("title", "the position")
        company = job_listing.get("company", "the company")
        description = job_listing.get("description", "")
        
        # Extract skills
        matched_skills = skill_profile.get("matched_skills", [])
        if isinstance(matched_skills, list) and matched_skills:
            if isinstance(matched_skills[0], dict):
                skills_list = [s.get("skill", str(s)) for s in matched_skills[:5]]
            else:
                skills_list = [str(s) for s in matched_skills[:5]]
        else:
            skills_list = ["Python", "FastAPI", "Docker", "PostgreSQL", "Automation"]
        
        skills_text = ", ".join(skills_list)
        
        # Determine length
        if length == "short":
            body_paragraphs = 2
        elif length == "long":
            body_paragraphs = 4
        else:  # medium
            body_paragraphs = 3
        
        # Build letter
        letter_parts = [
            "Dear Hiring Manager,",
            "",
            f"I am writing to express my strong interest in the {job_title} position at {company}."
        ]
        
        # Add body paragraphs
        if body_paragraphs >= 2:
            letter_parts.extend([
                "",
                f"With expertise in {skills_text}, I am confident that my technical background aligns well with your requirements. " +
                "I have extensive experience developing scalable applications and working with modern development practices."
            ])
        
        if body_paragraphs >= 3:
            letter_parts.extend([
                "",
                "I am particularly drawn to this opportunity because it allows me to leverage my skills in a challenging environment. " +
                "I am eager to contribute to your team and help drive innovation in your projects."
            ])
        
        if body_paragraphs >= 4:
            letter_parts.extend([
                "",
                "Throughout my career, I have demonstrated a strong ability to work collaboratively, solve complex problems, " +
                "and deliver high-quality solutions. I am excited about the possibility of bringing these strengths to your organization."
            ])
        
        letter_parts.extend([
            "",
            "Thank you for considering my application. I look forward to the opportunity to discuss how my experience and skills " +
            "can contribute to your team's success.",
            "",
            "Sincerely,",
            ""
        ])
        
        return "\n".join(letter_parts)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

