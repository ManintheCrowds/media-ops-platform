"""Verify that Adzuna jobs are properly saved to the database."""

import sys
import asyncio
import httpx
import json
from pathlib import Path

# Add the app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.job_listing import JobListing
from app.config import settings

BASE_URL = "http://localhost:8004"
LOG_PATH = Path(r"d:\CodeRepositories\.cursor\debug.log")

def log_entry(session_id, run_id, hypothesis_id, location, message, data):
    """Write debug log entry."""
    entry = {
        "sessionId": session_id,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(__import__('time').time() * 1000)
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

async def check_server_running():
    """Check if API server is running."""
    # #region agent log
    log_entry("verify-jobs", "run1", "H-SERVER", "verify_jobs_saved.py:check_server_running", "Checking if API server is running", {
        "base_url": BASE_URL
    })
    # #endregion agent log
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/health")
            # #region agent log
            log_entry("verify-jobs", "run1", "H-SERVER", "verify_jobs_saved.py:check_server_running", "Server health check result", {
                "status_code": response.status_code,
                "server_running": response.status_code == 200
            })
            # #endregion agent log
            return response.status_code == 200
    except Exception as e:
        # #region agent log
        log_entry("verify-jobs", "run1", "H-SERVER", "verify_jobs_saved.py:check_server_running", "Server not reachable", {
            "error": str(e),
            "error_type": type(e).__name__,
            "server_running": False
        })
        # #endregion agent log
        return False

def check_database_connection():
    """Check if database is accessible."""
    # #region agent log
    log_entry("verify-jobs", "run1", "H-DB", "verify_jobs_saved.py:check_database_connection", "Checking database connection", {
        "database_url": settings.database_url.split("@")[-1] if "@" in settings.database_url else "hidden"
    })
    # #endregion agent log
    
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            # #region agent log
            log_entry("verify-jobs", "run1", "H-DB", "verify_jobs_saved.py:check_database_connection", "Database connection successful", {
                "connected": True
            })
            # #endregion agent log
            return True
    except Exception as e:
        # #region agent log
        log_entry("verify-jobs", "run1", "H-DB", "verify_jobs_saved.py:check_database_connection", "Database connection failed", {
            "error": str(e),
            "error_type": type(e).__name__,
            "connected": False
        })
        # #endregion agent log
        return False

async def test_job_search_and_verify():
    """Test job search endpoint and verify jobs are saved."""
    print("=" * 80)
    print("VERIFYING JOB SEARCH AND DATABASE PERSISTENCE")
    print("=" * 80)
    print()
    
    # #region agent log
    log_entry("verify-jobs", "run1", "H0", "verify_jobs_saved.py:test_job_search_and_verify", "Starting verification", {})
    # #endregion agent log
    
    # Check prerequisites
    print("Checking prerequisites...")
    
    # Check database
    print("  Checking database connection...", end=" ", flush=True)
    db_ok = check_database_connection()
    if not db_ok:
        print("FAILED")
        print()
        print("=" * 80)
        print("ERROR: DATABASE NOT ACCESSIBLE")
        print("=" * 80)
        print()
        print("Cannot connect to PostgreSQL database.")
        print(f"Connection string: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'hidden'}")
        print()
        print("Make sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database 'jobautomation' exists")
        print("  3. Connection settings are correct in .env or environment variables")
        print()
        return False
    print("OK")
    
    # Check API server
    print("  Checking API server...", end=" ", flush=True)
    server_ok = await check_server_running()
    if not server_ok:
        print("FAILED")
        print()
        print("=" * 80)
        print("ERROR: API SERVER NOT RUNNING")
        print("=" * 80)
        print()
        print(f"Cannot connect to {BASE_URL}")
        print()
        print("Start the server with:")
        print("  cd d:\\software\\job-automation-service")
        print("  .\\restart_server.ps1")
        print()
        return False
    print("OK")
    print()
    
    # Get initial job count
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # #region agent log
    log_entry("verify-jobs", "run1", "H-DB-QUERY", "verify_jobs_saved.py:test_job_search_and_verify", "Querying initial job count", {})
    # #endregion agent log
    
    try:
        initial_count = db.query(JobListing).count()
        initial_adzuna_count = db.query(JobListing).filter(JobListing.source == "adzuna").count()
        print(f"Initial job count: {initial_count}")
        print(f"Initial Adzuna jobs: {initial_adzuna_count}")
        print()
    finally:
        db.close()
    
    # Test the search endpoint
    print("Testing /api/v1/jobs/search endpoint...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/jobs/search",
                json={
                    "query": "Python developer",
                    "location": "Minneapolis, MN",
                    "sources": ["adzuna"],
                    "limit": 10,
                    "min_match_score": 0.0
                }
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ Search endpoint returned: {response.status_code}")
            print(f"   Jobs returned in response: {data.get('count', 0)}")
            print(f"   Sources searched: {data.get('sources_searched', [])}")
            print()
            
            if data.get('count', 0) > 0:
                print("Sample jobs from response:")
                for i, job in enumerate(data.get('jobs', [])[:3], 1):
                    print(f"   {i}. {job.get('title')} at {job.get('company')}")
                    print(f"      Source: {job.get('source')}")
                    print(f"      Match Score: {job.get('overall_match_score', 0.0)}")
                print()
        except Exception as e:
            print(f"❌ Error calling search endpoint: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Wait a moment for database commit
    await asyncio.sleep(1)
    
    # Verify jobs in database
    print("Verifying jobs in database...")
    db = SessionLocal()
    try:
        final_count = db.query(JobListing).count()
        final_adzuna_count = db.query(JobListing).filter(JobListing.source == "adzuna").count()
        new_jobs = final_count - initial_count
        new_adzuna_jobs = final_adzuna_count - initial_adzuna_count
        
        print(f"Final job count: {final_count}")
        print(f"Final Adzuna jobs: {final_adzuna_count}")
        print(f"New jobs added: {new_jobs}")
        print(f"New Adzuna jobs added: {new_adzuna_jobs}")
        print()
        
        if new_adzuna_jobs > 0:
            print("✅ SUCCESS: Adzuna jobs were saved to database!")
            print()
            print("Sample saved Adzuna jobs:")
            adzuna_jobs = db.query(JobListing).filter(
                JobListing.source == "adzuna"
            ).order_by(JobListing.id.desc()).limit(5).all()
            
            for i, job in enumerate(adzuna_jobs, 1):
                print(f"   {i}. {job.title} at {job.company}")
                print(f"      Source: {job.source}")
                print(f"      Source ID: {job.source_id}")
                print(f"      Match Score: {job.overall_match_score}")
                print(f"      Has Description: {bool(job.description)}")
                print(f"      URL: {job.url[:80]}..." if len(job.url) > 80 else f"      URL: {job.url}")
                print()
            
            # Verify data quality
            jobs_with_scores = db.query(JobListing).filter(
                JobListing.source == "adzuna",
                JobListing.overall_match_score > 0.0
            ).count()
            
            jobs_with_descriptions = db.query(JobListing).filter(
                JobListing.source == "adzuna",
                JobListing.description.isnot(None),
                JobListing.description != ""
            ).count()
            
            print("Data Quality Check:")
            print(f"   Jobs with match scores > 0: {jobs_with_scores}/{final_adzuna_count}")
            print(f"   Jobs with descriptions: {jobs_with_descriptions}/{final_adzuna_count}")
            print()
            
            return True
        else:
            print("❌ WARNING: No new Adzuna jobs were saved to database")
            print("   This indicates the database commit may have failed")
            return False
            
    finally:
        db.close()

if __name__ == "__main__":
    print()
    success = asyncio.run(test_job_search_and_verify())
    print("=" * 80)
    if success:
        print("VERIFICATION COMPLETE: Jobs are being saved correctly")
    else:
        print("VERIFICATION FAILED: Jobs are not being saved")
    print("=" * 80)
    sys.exit(0 if success else 1)


