"""Fetch all jobs directly from the database."""

import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

# Add the app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.job_listing import JobListing
from app.config import settings

def get_all_jobs():
    """Get all jobs from the database."""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get all jobs
        jobs = db.query(JobListing).order_by(JobListing.id).all()
        
        # Convert to dict
        jobs_data = []
        for job in jobs:
            job_dict = {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "source": job.source,
                "source_id": job.source_id,
                "url": job.url,
                "description": job.description,
                "requirements": job.requirements,
                "salary_range": job.salary_range,
                "job_type": job.job_type,
                "remote": job.remote,
                "skill_match_score": job.skill_match_score,
                "experience_match_score": job.experience_match_score,
                "overall_match_score": job.overall_match_score,
                "scraped_at": job.scraped_at.isoformat() if job.scraped_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                "is_active": job.is_active
            }
            jobs_data.append(job_dict)
        
        return jobs_data
    finally:
        db.close()

if __name__ == "__main__":
    print("Fetching all jobs from database...")
    try:
        all_jobs = get_all_jobs()
        print(f"\nFound {len(all_jobs)} jobs\n")
        
        # Print summary
        print("=" * 80)
        print("ALL DISCOVERED JOBS")
        print("=" * 80)
        print()
        
        for i, job in enumerate(all_jobs, 1):
            print(f"{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Source: {job['source'] or 'LinkedIn'}")
            print(f"   URL: {job['url']}")
            print(f"   Match Score: {job['overall_match_score']}")
            print(f"   Active: {job['is_active']}")
            print()
        
        # Export to JSON
        output_file = "all_jobs_export.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, indent=2, default=str)
        
        print(f"\n[OK] Exported all {len(all_jobs)} jobs to {output_file}")
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch jobs: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database connection is configured correctly")
        print("  3. You're in the job-automation-service directory")
        import traceback
        traceback.print_exc()
        sys.exit(1)

