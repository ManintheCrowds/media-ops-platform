"""Detailed endpoint test with error checking."""

import httpx
import json
import sys

BASE_URL = "http://localhost:8004"

def test():
    """Test endpoint with detailed error checking."""
    print("=" * 60)
    print("Detailed Endpoint Test")
    print("=" * 60)
    print()
    
    # Check health
    try:
        health = httpx.get(f"{BASE_URL}/health", timeout=5.0)
        print(f"Health check: {health.status_code}")
    except Exception as e:
        print(f"[ERROR] Cannot connect to server: {e}")
        return
    
    # Test with Adzuna
    search_data = {
        "query": "Python developer",
        "location": "Minneapolis, MN",
        "sources": ["adzuna"],
        "limit": 10,
        "min_match_score": 0.0  # Set to 0 to avoid filtering
    }
    
    print(f"Request: {json.dumps(search_data, indent=2)}")
    print()
    
    try:
        response = httpx.post(
            f"{BASE_URL}/api/v1/jobs/search",
            json=search_data,
            timeout=60.0
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            sources = data.get("sources_searched", [])
            count = data.get("count", 0)
            
            print(f"Response: {json.dumps(data, indent=2, default=str)}")
            print()
            print(f"Jobs found: {len(jobs)}")
            print(f"Count field: {count}")
            print(f"Sources searched: {sources}")
            
            if not sources:
                print()
                print("[WARNING] sources_searched is empty - exception may have occurred")
                print("Check server logs for errors")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()

