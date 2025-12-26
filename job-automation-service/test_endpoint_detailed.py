"""Test endpoint with detailed logging."""

import httpx
import json
from app.config import settings

print("=" * 80)
print("DETAILED ENDPOINT TEST")
print("=" * 80)
print(f"Adzuna API ID: {settings.adzuna_api_id}")
print(f"Adzuna API Key: {'Set' if settings.adzuna_api_key else 'NOT SET'}")
print()

# Test health
print("[1] Testing health endpoint...")
try:
    response = httpx.get("http://localhost:8004/health", timeout=5.0)
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
except Exception as e:
    print(f"  ERROR: {e}")
    exit(1)

print()
print("[2] Testing job search endpoint...")
body = {
    "query": "python",
    "location": "Minneapolis, MN",
    "limit": 10,
    "sources": ["adzuna"]
}

try:
    response = httpx.post(
        "http://localhost:8004/api/v1/jobs/search",
        json=body,
        timeout=30.0
    )
    print(f"  Status: {response.status_code}")
    data = response.json()
    print(f"  Jobs found: {data.get('count', 0)}")
    print(f"  Sources searched: {data.get('sources_searched', [])}")
    
    if data.get('count', 0) == 0:
        print("\n  [WARN] No jobs returned. Possible issues:")
        print("    - Server may need restart to load .env credentials")
        print("    - Adzuna API may have rate limits")
        print("    - Check server logs for errors")
    else:
        print(f"\n  [OK] Found {data['count']} jobs")
        if data.get('jobs'):
            print(f"  First job: {data['jobs'][0].get('title', 'N/A')} at {data['jobs'][0].get('company', 'N/A')}")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

print()
print("[3] Checking database for new jobs...")
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.job_listing import JobListing

try:
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Count jobs by source
    total = db.query(JobListing).count()
    adzuna_count = db.query(JobListing).filter(JobListing.source == "adzuna").count()
    with_source = db.query(JobListing).filter(JobListing.source != None, JobListing.source != "").count()
    
    print(f"  Total jobs: {total}")
    print(f"  Adzuna jobs: {adzuna_count}")
    print(f"  Jobs with source: {with_source}")
    
    # Get most recent job
    recent = db.query(JobListing).order_by(JobListing.id.desc()).first()
    if recent:
        print(f"  Most recent: ID={recent.id}, Title={recent.title}, Source={recent.source or 'empty'}")
    
    db.close()
except Exception as e:
    print(f"  ERROR: {e}")

print()
print("=" * 80)
