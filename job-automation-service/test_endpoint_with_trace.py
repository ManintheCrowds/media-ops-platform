"""Test endpoint with full error tracing."""

import httpx
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("ENDPOINT TEST WITH FULL TRACING")
print("=" * 80)
print()

# Test the endpoint
body = {
    "query": "python",
    "location": "Minneapolis, MN",
    "limit": 5,
    "sources": ["adzuna"]
}

print("Calling endpoint...")
try:
    response = httpx.post(
        "http://localhost:8004/api/v1/jobs/search",
        json=body,
        timeout=30.0
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Jobs found: {data.get('count', 0)}")
        print(f"Sources searched: {data.get('sources_searched', [])}")
        
        if data.get('count', 0) == 0:
            print()
            print("[WARN] No jobs returned!")
            print("Full response:")
            print(json.dumps(data, indent=2))
            
            # Check for any error fields
            if 'error' in data:
                print(f"\nError in response: {data['error']}")
            if 'message' in data:
                print(f"Message: {data['message']}")
        else:
            print(f"\n[SUCCESS] Found {data['count']} jobs!")
            if data.get('jobs'):
                print(f"First job: {data['jobs'][0].get('title', 'N/A')}")
    else:
        print(f"[ERROR] Status {response.status_code}")
        print(f"Response: {response.text}")
        
except httpx.RequestError as e:
    print(f"[ERROR] Request failed: {e}")
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("IMPORTANT: Check the SERVER CONSOLE WINDOW for:")
print("  1. 'SERVER STARTUP - CREDENTIALS CHECK' section")
print("  2. [DEBUG] messages when endpoint is called")
print("  3. Any [ENDPOINT ERROR] messages")
print("=" * 80)






