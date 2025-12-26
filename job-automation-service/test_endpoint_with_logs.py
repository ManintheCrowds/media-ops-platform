"""Test endpoint and check server logs for errors."""

import httpx
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings

print("=" * 80)
print("ENDPOINT TEST WITH LOGGING")
print("=" * 80)
print()

# Test credentials in this process
print("Local process credentials:")
print(f"  Adzuna API ID: {settings.adzuna_api_id}")
print(f"  Adzuna API Key: {'Set' if settings.adzuna_api_key else 'NOT SET'}")
print()

# Test endpoint
print("Testing endpoint...")
body = {
    "query": "python",
    "location": "Minneapolis, MN",
    "limit": 5,
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
        print()
        print("  [WARN] No jobs returned!")
        print("  Checking response details...")
        print(f"  Response keys: {list(data.keys())}")
        
        if 'jobs' in data:
            print(f"  Jobs list length: {len(data['jobs'])}")
            if data['jobs']:
                print(f"  First job: {data['jobs'][0]}")
        
        # Check for error messages
        if 'error' in data:
            print(f"  Error: {data['error']}")
        if 'message' in data:
            print(f"  Message: {data['message']}")
    else:
        print(f"  [OK] Found {data['count']} jobs")
        if data.get('jobs'):
            print(f"  First job: {data['jobs'][0].get('title', 'N/A')}")
            
except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("Next steps:")
print("1. Check server console window for [DEBUG] and [ERROR] messages")
print("2. Check if server process has .env file in its working directory")
print("3. Verify server can access credentials by checking server logs")
print("=" * 80)

