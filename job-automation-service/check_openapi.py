#!/usr/bin/env python3
"""Check OpenAPI schema for scheduler routes."""
import httpx
import json

BASE_URL = "http://localhost:8004"

try:
    response = httpx.get(f"{BASE_URL}/openapi.json")
    response.raise_for_status()
    openapi = response.json()
    scheduler_routes = [path for path in openapi.get('paths', {}).keys() if 'scheduler' in path]
    print("Scheduler routes in OpenAPI schema:")
    print(json.dumps(sorted(scheduler_routes), indent=2))
    
    # Check specifically for start/stop
    start_stop = [path for path in scheduler_routes if 'start' in path or 'stop' in path]
    print(f"\nStart/Stop routes found: {len(start_stop)}")
    if start_stop:
        print("  " + "\n  ".join(start_stop))
    else:
        print("  [WARNING] Start/Stop routes NOT found in OpenAPI schema!")
        
except httpx.RequestError as e:
    print(f"Error connecting to server: {e}")
    print("Make sure the server is running on http://localhost:8004")
except Exception as e:
    print(f"Error: {e}")

