"""Test if server process can access credentials."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.services.api_clients.adzuna_api import AdzunaAPIClient
import asyncio

async def test():
    print("=" * 80)
    print("TESTING SERVER CREDENTIALS ACCESS")
    print("=" * 80)
    print()
    
    print("Configuration:")
    print(f"  Adzuna API ID: {settings.adzuna_api_id}")
    print(f"  Adzuna API Key: {'Set' if settings.adzuna_api_key else 'NOT SET'}")
    print()
    
    print("Creating AdzunaAPIClient...")
    try:
        client = AdzunaAPIClient()
        print(f"  Client created: {client}")
        print(f"  Client source_name: {client.source_name}")
        print(f"  Client has API key: {bool(client.api_key)}")
        print(f"  Client has API ID: {bool(client.api_id)}")
        print()
        
        print("Testing Adzuna API call...")
        jobs = await client.search_jobs("python", "Minneapolis, MN", limit=5)
        print(f"  Jobs returned: {len(jobs)}")
        
        if jobs:
            print(f"  First job: {jobs[0].get('title', 'N/A')} at {jobs[0].get('company', {}).get('display_name', 'N/A')}")
            print(f"  Job source: {jobs[0].get('source', 'N/A')}")
        else:
            print("  [WARN] No jobs returned from Adzuna API")
            print("  This could indicate:")
            print("    - API credentials not working")
            print("    - Rate limiting")
            print("    - API endpoint issue")
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())

