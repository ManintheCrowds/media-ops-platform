"""Test if server process can load .env file from explicit path."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("TESTING SERVER ENV FILE LOADING")
print("=" * 80)
print()

# Simulate what happens when server starts
print("1. Testing _find_env_file() function...")
from app.config import _find_env_file
env_path = _find_env_file()
print(f"   Env file path: {env_path}")
print(f"   Exists: {Path(env_path).exists()}")
print()

print("2. Testing Settings class instantiation...")
from app.config import settings
print(f"   Adzuna API ID: {settings.adzuna_api_id}")
print(f"   Adzuna API Key: {'Set' if settings.adzuna_api_key else 'NOT SET'}")
print(f"   JSearch API Key: {'Set' if settings.jsearch_api_key else 'NOT SET'}")
print()

print("3. Testing JobSourceManager creation...")
from app.services.job_source_manager import JobSourceManager
manager = JobSourceManager()
print(f"   Has Adzuna client: {manager.has_api_client('adzuna')}")
print(f"   Adzuna client object: {manager.api_clients.get('adzuna')}")
print()

if not manager.has_api_client('adzuna'):
    print("[ERROR] JobSourceManager doesn't have Adzuna client!")
    print("This means settings.adzuna_api_key or settings.adzuna_api_id is None/empty")
    print()
    print("Debugging:")
    print(f"  settings.adzuna_api_id = {repr(settings.adzuna_api_id)}")
    print(f"  settings.adzuna_api_key = {repr(settings.adzuna_api_key[:20] + '...' if settings.adzuna_api_key else None)}")
else:
    print("[OK] JobSourceManager has Adzuna client configured")
    print()
    print("4. Testing Adzuna API call...")
    import asyncio
    async def test():
        jobs = await manager.search_via_api("adzuna", "python", "Minneapolis, MN", 3)
        print(f"   Jobs returned: {len(jobs)}")
        if jobs:
            print(f"   First job: {jobs[0].get('title', 'N/A')}")
    
    asyncio.run(test())

print()
print("=" * 80)

