"""Test endpoint code directly without HTTP."""

import asyncio
from app.api.jobs import search_jobs
from app.schemas.job import JobSearchRequest
from app.database import SessionLocal

async def test_direct():
    """Test the search_jobs function directly."""
    print("Testing search_jobs function directly...")
    print()
    
    db = SessionLocal()
    
    try:
        request = JobSearchRequest(
            query="Python developer",
            location="Minneapolis, MN",
            sources=["adzuna"],
            limit=10,
            min_match_score=0.0
        )
        
        print(f"Request: query={request.query}, sources={request.sources}")
        print()
        
        result = await search_jobs(request, db)
        
        print(f"Result:")
        print(f"  Jobs: {len(result.jobs)}")
        print(f"  Count: {result.count}")
        print(f"  Sources searched: {result.sources_searched}")
        print()
        
        if result.jobs:
            print("Sample jobs:")
            for i, job in enumerate(result.jobs[:3], 1):
                print(f"  {i}. {job.title}")
                print(f"     {job.company} - {job.location}")
        else:
            print("[WARNING] No jobs returned")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_direct())

