"""Test Adzuna API via the endpoint."""

import httpx
import json

BASE_URL = "http://localhost:8004"

def test_adzuna():
    """Test Adzuna API through the endpoint."""
    print("=" * 60)
    print("Testing Adzuna API via /api/v1/jobs/search")
    print("=" * 60)
    print()
    
    try:
        # Check if service is running
        health = httpx.get(f"{BASE_URL}/health", timeout=5.0)
        if health.status_code != 200:
            print("[ERROR] Service is not healthy")
            return
    except httpx.ConnectError:
        print("[ERROR] Service is not running")
        print("  Start with: .\\start_service.ps1")
        return
    
    # Test search with Adzuna
    search_data = {
        "query": "Python developer",
        "location": "Minneapolis, MN",
        "sources": ["adzuna"],
        "limit": 10,
        "min_match_score": 0.0
    }
    
    print("Request:")
    print(f"  Query: {search_data['query']}")
    print(f"  Location: {search_data['location']}")
    print(f"  Sources: {search_data['sources']}")
    print()
    
    try:
        response = httpx.post(
            f"{BASE_URL}/api/v1/jobs/search",
            json=search_data,
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            sources = data.get("sources_searched", [])
            
            print(f"[SUCCESS] API returned {len(jobs)} jobs")
            print(f"  Sources searched: {sources}")
            print()
            
            if not sources:
                print("[ERROR] sources_searched is empty - exception occurred!")
                print("  Check server console for error messages.")
                print("  Server may need restart to pick up code changes.")
            elif jobs:
                print("Sample jobs:")
                for i, job in enumerate(jobs[:5], 1):
                    print(f"  {i}. {job.get('title', 'N/A')}")
                    print(f"     {job.get('company', 'N/A')} - {job.get('location', 'N/A')}")
                    print(f"     Source: {job.get('source', 'N/A')}")
                    print()
            else:
                print("[WARNING] No jobs returned (might be filtered by match score)")
                print(f"  But sources_searched shows: {sources} - search was attempted")
        else:
            print(f"[ERROR] API returned status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_adzuna()

