"""Test JobSourceManager directly."""

import asyncio
from app.services.job_source_manager import JobSourceManager

async def test():
    """Test JobSourceManager with Adzuna."""
    print("Testing JobSourceManager with Adzuna...")
    print()
    
    manager = JobSourceManager()
    
    try:
        print("Checking API client availability...")
        print(f"  Adzuna available: {manager.has_api_client('adzuna')}")
        print()
        
        print("Searching for 'Python developer' in 'Minneapolis, MN'...")
        jobs = await manager.search_jobs(
            query="Python developer",
            location="Minneapolis, MN",
            sources=["adzuna"],
            limit=10
        )
        
        print(f"Found {len(jobs)} jobs")
        print()
        
        if jobs:
            print("Sample jobs:")
            for i, job in enumerate(jobs[:5], 1):
                print(f"  {i}. [{job.get('source', 'unknown')}] {job.get('title', 'N/A')}")
                print(f"     {job.get('company', 'N/A')} - {job.get('location', 'N/A')}")
        else:
            print("[WARNING] No jobs found")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(test())

