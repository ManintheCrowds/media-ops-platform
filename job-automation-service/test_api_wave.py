"""Comprehensive API test suite - makes multiple calls to test all endpoints."""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8004"

def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_result(endpoint: str, status: str, data: Any = None):
    """Print a formatted test result."""
    color = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{color} {endpoint}: {status}")
    if data:
        if isinstance(data, dict):
            print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"   Response: {str(data)[:200]}...")

def test_health():
    """Test health endpoint."""
    print_section("HEALTH CHECK")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_result("/health", "PASS", data)
            return True
        else:
            print_result("/health", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("/health", "FAIL", str(e))
        return False

def test_debug_credentials():
    """Test debug credentials endpoint."""
    print_section("DEBUG CREDENTIALS")
    try:
        response = requests.get(f"{BASE_URL}/debug/credentials", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_result("/debug/credentials", "PASS", data)
            print(f"   Has Adzuna Client: {data.get('has_adzuna_client', False)}")
            print(f"   Adzuna API ID: {data.get('adzuna_api_id_value', 'N/A')}")
            return True
        else:
            print_result("/debug/credentials", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("/debug/credentials", "FAIL", str(e))
        return False

def test_job_search(query: str = "python", location: str = "Minneapolis, MN", sources: list = None):
    """Test job search endpoint."""
    print_section(f"JOB SEARCH: '{query}' in {location}")
    if sources is None:
        sources = ["adzuna"]
    
    payload = {
        "query": query,
        "location": location,
        "limit": 10,
        "sources": sources
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/jobs/search",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", 0)
            jobs = data.get("jobs", [])
            sources_searched = data.get("sources_searched", [])
            
            print_result("/api/v1/jobs/search", "PASS" if count > 0 else "WARN", {
                "count": count,
                "sources_searched": sources_searched,
                "first_job": jobs[0] if jobs else None
            })
            
            if count > 0:
                print(f"   ✅ Found {count} jobs")
                if jobs:
                    first = jobs[0]
                    print(f"   First job: {first.get('title', 'N/A')} at {first.get('company', 'N/A')}")
                    print(f"   Source: {first.get('source', 'N/A')}")
                    print(f"   URL: {first.get('url', 'N/A')[:80]}...")
            else:
                print(f"   ⚠️  No jobs returned (check server console for details)")
            
            return count > 0
        else:
            print_result("/api/v1/jobs/search", "FAIL", f"Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print_result("/api/v1/jobs/search", "FAIL", str(e))
        return False

def test_list_jobs(limit: int = 10):
    """Test list jobs endpoint."""
    print_section(f"LIST JOBS (limit={limit})")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/jobs?limit={limit}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            count = len(jobs)
            print_result("/api/v1/jobs", "PASS", {"count": count})
            if count > 0:
                print(f"   ✅ Found {count} jobs in database")
                if jobs:
                    first = jobs[0]
                    print(f"   First job: {first.get('title', 'N/A')} at {first.get('company', 'N/A')}")
            else:
                print(f"   ⚠️  No jobs in database")
            return True
        else:
            print_result("/api/v1/jobs", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("/api/v1/jobs", "FAIL", str(e))
        return False

def test_recommended_jobs(min_score: float = 0.7, limit: int = 10):
    """Test recommended jobs endpoint."""
    print_section(f"RECOMMENDED JOBS (min_score={min_score})")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/jobs/recommended?min_score={min_score}&limit={limit}",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            count = len(jobs)
            print_result("/api/v1/jobs/recommended", "PASS" if count > 0 else "WARN", {"count": count})
            if count > 0:
                print(f"   ✅ Found {count} recommended jobs")
            else:
                print(f"   ⚠️  No recommended jobs (may need jobs with match scores)")
            return True
        else:
            print_result("/api/v1/jobs/recommended", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("/api/v1/jobs/recommended", "FAIL", str(e))
        return False

def test_multiple_searches():
    """Test multiple search queries."""
    print_section("MULTIPLE SEARCH QUERIES")
    
    queries = [
        ("python", "Minneapolis, MN"),
        ("python developer", "Minneapolis, MN"),
        ("fastapi", "Minneapolis, MN"),
        ("software engineer", "Minneapolis, MN"),
    ]
    
    results = []
    for query, location in queries:
        print(f"\n  Testing: '{query}' in {location}")
        success = test_job_search(query, location, ["adzuna"])
        results.append((query, success))
        time.sleep(1)  # Rate limiting
    
    print(f"\n  Summary:")
    for query, success in results:
        status = "✅" if success else "❌"
        print(f"    {status} {query}")
    
    return all(success for _, success in results)

def main():
    """Run all API tests."""
    print("\n" + "=" * 80)
    print("  COMPREHENSIVE API TEST SUITE")
    print("=" * 80)
    print(f"\nTesting API at: {BASE_URL}")
    print("Make sure the server is running!\n")
    
    results = []
    
    # Basic health checks
    results.append(("Health", test_health()))
    time.sleep(0.5)
    
    results.append(("Debug Credentials", test_debug_credentials()))
    time.sleep(0.5)
    
    # Job search tests
    results.append(("Job Search (python)", test_job_search("python", "Minneapolis, MN", ["adzuna"])))
    time.sleep(1)
    
    # List jobs
    results.append(("List Jobs", test_list_jobs(10)))
    time.sleep(0.5)
    
    # Recommended jobs
    results.append(("Recommended Jobs", test_recommended_jobs(0.7, 10)))
    time.sleep(0.5)
    
    # Multiple searches
    results.append(("Multiple Searches", test_multiple_searches()))
    
    # Final summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed!")
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed - check server console for details")

if __name__ == "__main__":
    main()



