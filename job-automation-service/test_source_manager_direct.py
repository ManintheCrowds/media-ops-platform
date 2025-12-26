"""Test JobSourceManager directly to see if it has credentials."""

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.job_source_manager import JobSourceManager
from app.config import settings

async def test():
    print("=" * 80)
    print("TESTING JOBSOURCEMANAGER")
    print("=" * 80)
    print()
    
    print("Configuration:")
    print(f"  Adzuna API ID: {settings.adzuna_api_id}")
    print(f"  Adzuna API Key: {'Set' if settings.adzuna_api_key else 'NOT SET'}")
    print()
    
    print("Creating JobSourceManager...")
    manager = JobSourceManager()
    
    print(f"  Has Adzuna client: {manager.has_api_client('adzuna')}")
    print(f"  Adzuna client object: {manager.api_clients.get('adzuna')}")
    print()
    
    if not manager.has_api_client('adzuna'):
        print("[ERROR] Adzuna client not available in JobSourceManager!")
        print("This means the server process doesn't have credentials loaded.")
        return
    
    print("Testing search_via_api...")
    try:
        jobs = await manager.search_via_api("adzuna", "python", "Minneapolis, MN", 5)
        print(f"  Jobs returned: {len(jobs)}")
        
        if jobs:
            print(f"  First job: {jobs[0].get('title', 'N/A')} at {jobs[0].get('company', 'N/A')}")
            print(f"  Job source: {jobs[0].get('source', 'N/A')}")
        else:
            print("  [WARN] No jobs returned")
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("Testing full search_jobs method...")
    try:
        all_jobs, sources = await manager.search_jobs(
            query="python",
            location="Minneapolis, MN",
            sources=["adzuna"],
            limit=5
        )
        print(f"  Total jobs: {len(all_jobs)}")
        print(f"  Sources searched: {sources}")
        
        if all_jobs:
            print(f"  First job: {all_jobs[0].get('title', 'N/A')}")
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())

