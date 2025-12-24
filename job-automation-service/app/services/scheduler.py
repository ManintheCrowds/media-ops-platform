"""Scheduled job search service."""

import logging
import asyncio
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.job_listing import JobListing
from app.services.job_api import (
    IndeedScraper,
    LinkedInScraper,
    GlassdoorScraper,
    ZipRecruiterScraper
)
from app.services.skill_matcher import SkillMatcher

logger = logging.getLogger(__name__)

# Default search queries
DEFAULT_QUERIES = [
    "Python developer",
    "FastAPI developer",
    "DevOps engineer",
    "Automation engineer",
    "Infrastructure engineer",
    "API developer",
    "Backend developer",
    "Software engineer Python",
]


async def run_scheduled_search(
    queries: List[str] = None,
    location: str = "Minneapolis, MN",
    sources: List[str] = None,
    min_match_score: float = 0.7,
    limit_per_query: int = 10
):
    """Run scheduled job search.
    
    Args:
        queries: List of search queries (defaults to DEFAULT_QUERIES)
        location: Location string
        sources: List of sources to search (defaults to all)
        min_match_score: Minimum match score to save
        limit_per_query: Maximum jobs per query
    """
    queries = queries or DEFAULT_QUERIES
    sources = sources or ["adzuna", "indeed", "linkedin", "glassdoor", "ziprecruiter"]
    
    db: Session = SessionLocal()
    scrapers = []
    
    try:
        logger.info(f"Starting scheduled job search: {len(queries)} queries, {len(sources)} sources")
        
        # Initialize scrapers
        scraper_classes = {
            "indeed": IndeedScraper,
            "linkedin": LinkedInScraper,
            "glassdoor": GlassdoorScraper,
            "ziprecruiter": ZipRecruiterScraper,
        }
        
        for source in sources:
            if source in scraper_classes:
                scrapers.append(scraper_classes[source]())
        
        # Initialize matcher
        matcher = SkillMatcher(db)
        
        total_found = 0
        total_saved = 0
        
        # Search each query
        for query in queries:
            logger.info(f"Searching for: {query}")
            
            all_jobs = []
            
            # Search each source
            for scraper in scrapers:
                try:
                    jobs = await scraper.search_jobs(
                        query=query,
                        location=location,
                        limit=limit_per_query
                    )
                    all_jobs.extend(jobs)
                except Exception as e:
                    logger.error(f"Error searching {scraper.source_name} for '{query}': {e}")
            
            total_found += len(all_jobs)
            
            # Process and save jobs
            for job_data in all_jobs:
                # Check if job already exists
                existing = db.query(JobListing).filter(
                    JobListing.source == job_data.get("source", ""),
                    JobListing.source_id == job_data.get("source_id")
                ).first()
                
                if existing:
                    # Update existing job
                    job_listing = existing
                else:
                    # Create new job listing
                    job_listing = JobListing(
                        title=job_data.get("title", ""),
                        company=job_data.get("company", ""),
                        location=job_data.get("location"),
                        source=job_data.get("source", ""),
                        source_id=job_data.get("source_id"),
                        url=job_data.get("url", ""),
                        description=job_data.get("description"),
                        requirements=job_data.get("requirements"),
                        salary_range=job_data.get("salary_range"),
                        job_type=job_data.get("job_type"),
                        remote=job_data.get("remote", False),
                        raw_data=job_data.get("raw_data"),
                    )
                    db.add(job_listing)
                
                # Calculate match scores
                description = job_listing.description or ""
                scores = matcher.calculate_match_score(description)
                
                job_listing.skill_match_score = scores["skill_match_score"]
                job_listing.experience_match_score = scores["experience_match_score"]
                job_listing.overall_match_score = scores["overall_match_score"]
                job_listing.updated_at = datetime.utcnow()
                
                # Only save if meets minimum score
                if scores["overall_match_score"] >= min_match_score:
                    total_saved += 1
            
            db.commit()
        
        logger.info(f"Scheduled search complete: {total_found} jobs found, {total_saved} saved (score >= {min_match_score})")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in scheduled job search: {e}")
        raise
    finally:
        # Cleanup scrapers
        for scraper in scrapers:
            try:
                await scraper.close()
            except Exception as e:
                logger.warning(f"Error closing scraper: {e}")
        db.close()


async def run_daily_search():
    """Run daily job search (can be called by cron or scheduler)."""
    await run_scheduled_search(
        queries=DEFAULT_QUERIES,
        location="Minneapolis, MN",
        min_match_score=0.7,
        limit_per_query=10
    )


async def run_weekly_search():
    """Run weekly job search with more comprehensive results."""
    await run_scheduled_search(
        queries=DEFAULT_QUERIES,
        location="Minneapolis, MN",
        min_match_score=0.6,  # Lower threshold for weekly
        limit_per_query=25  # More results
    )

