"""Backfill source fields and calculate match scores for legacy jobs in database."""

import sys
from pathlib import Path

# Add the app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.job_listing import JobListing
from app.services.skill_matcher import SkillMatcher
from app.config import settings

def backfill_legacy_jobs():
    """Backfill source fields and calculate match scores for legacy jobs."""
    print("=" * 80)
    print("BACKFILLING LEGACY JOBS")
    print("=" * 80)
    print()
    
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Find jobs with empty source or zero match scores
        jobs_to_update = db.query(JobListing).filter(
            (JobListing.source == "") | 
            (JobListing.source == None) |
            (JobListing.overall_match_score == 0.0)
        ).all()
        
        total_jobs = len(jobs_to_update)
        print(f"Found {total_jobs} jobs to update")
        print()
        
        if total_jobs == 0:
            print("✅ No legacy jobs found - all jobs are up to date!")
            return
        
        # Initialize skill matcher
        print("Initializing skill matcher...")
        matcher = SkillMatcher(db)
        print("✅ Skill matcher initialized")
        print()
        
        # Process jobs
        updated_source = 0
        updated_scores = 0
        errors = 0
        
        for i, job in enumerate(jobs_to_update, 1):
            print(f"Processing job {i}/{total_jobs}: {job.title} at {job.company}")
            
            # Backfill source field
            if not job.source or job.source == "":
                if job.source_id:
                    # Infer source from source_id
                    if job.source_id.startswith("linkedin_"):
                        job.source = "linkedin"
                        updated_source += 1
                        print(f"   ✅ Set source to 'linkedin' (from source_id)")
                    elif job.source_id.startswith("indeed_"):
                        job.source = "indeed"
                        updated_source += 1
                        print(f"   ✅ Set source to 'indeed' (from source_id)")
                    elif job.source_id.startswith("glassdoor_"):
                        job.source = "glassdoor"
                        updated_source += 1
                        print(f"   ✅ Set source to 'glassdoor' (from source_id)")
                    elif job.source_id.startswith("ziprecruiter_"):
                        job.source = "ziprecruiter"
                        updated_source += 1
                        print(f"   ✅ Set source to 'ziprecruiter' (from source_id)")
                    else:
                        # Default to unknown if we can't infer
                        job.source = "unknown"
                        updated_source += 1
                        print(f"   ⚠️  Set source to 'unknown' (could not infer from source_id)")
                else:
                    # No source_id either - set to unknown
                    job.source = "unknown"
                    updated_source += 1
                    print(f"   ⚠️  Set source to 'unknown' (no source_id)")
            
            # Calculate match scores if they're zero
            if job.overall_match_score == 0.0:
                description = job.description or ""
                if description:
                    try:
                        scores = matcher.calculate_match_score(description)
                        job.skill_match_score = scores.get("skill_match_score", 0.0)
                        job.experience_match_score = scores.get("experience_match_score", 0.0)
                        job.overall_match_score = scores.get("overall_match_score", 0.0)
                        updated_scores += 1
                        print(f"   ✅ Calculated match scores: {job.overall_match_score:.3f}")
                    except Exception as e:
                        errors += 1
                        print(f"   ❌ Error calculating scores: {e}")
                else:
                    print(f"   ⚠️  No description available - skipping score calculation")
            
            # Commit every 10 jobs to avoid long transactions
            if i % 10 == 0:
                try:
                    db.commit()
                    print(f"   💾 Committed batch of 10 jobs")
                except Exception as e:
                    print(f"   ❌ Error committing batch: {e}")
                    db.rollback()
                    errors += 1
        
        # Final commit
        print()
        print("Committing final changes...")
        try:
            db.commit()
            print("✅ All changes committed successfully")
        except Exception as e:
            print(f"❌ Error committing final changes: {e}")
            db.rollback()
            errors += 1
        
        # Print summary
        print()
        print("=" * 80)
        print("BACKFILL SUMMARY")
        print("=" * 80)
        print(f"Total jobs processed: {total_jobs}")
        print(f"Source fields updated: {updated_source}")
        print(f"Match scores calculated: {updated_scores}")
        print(f"Errors encountered: {errors}")
        print()
        
        # Verify results
        print("Verifying results...")
        jobs_with_source = db.query(JobListing).filter(
            JobListing.source != "",
            JobListing.source != None
        ).count()
        
        jobs_with_scores = db.query(JobListing).filter(
            JobListing.overall_match_score > 0.0
        ).count()
        
        total_jobs_in_db = db.query(JobListing).count()
        
        print(f"Total jobs in database: {total_jobs_in_db}")
        print(f"Jobs with source field: {jobs_with_source}")
        print(f"Jobs with match scores > 0: {jobs_with_scores}")
        print()
        
        if jobs_with_source == total_jobs_in_db and jobs_with_scores > 0:
            print("✅ SUCCESS: All legacy jobs have been updated!")
        else:
            print("⚠️  WARNING: Some jobs may still need updating")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print()
    try:
        backfill_legacy_jobs()
        print("=" * 80)
        print("BACKFILL COMPLETE")
        print("=" * 80)
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Backfill interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


