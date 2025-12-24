"""Test script for aggregator API integrations."""

import asyncio
import sys
import os

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app.config import settings
from app.services.api_clients.adzuna_api import AdzunaAPIClient
from app.services.api_clients.jsearch_api import JSearchAPIClient
from app.services.job_source_manager import JobSourceManager


async def test_adzuna_api():
    """Test Adzuna API client."""
    print("=" * 60)
    print("Testing Adzuna API")
    print("=" * 60)
    
    if not settings.adzuna_api_key or not settings.adzuna_api_id:
        print("[SKIP] Adzuna API credentials not configured")
        return False
    
    print(f"API ID: {settings.adzuna_api_id[:10]}...")
    print(f"API Key: {'*' * 20}")
    print()
    
    client = AdzunaAPIClient()
    
    try:
        print("Searching for 'Python developer' in 'Minneapolis, MN'...")
        jobs = await client.search_jobs("Python developer", "Minneapolis, MN", limit=5)
        
        if jobs:
            print(f"[SUCCESS] Found {len(jobs)} jobs")
            print()
            for i, job in enumerate(jobs[:3], 1):
                print(f"  {i}. {job.get('title', 'N/A')}")
                print(f"     Company: {job.get('company', 'N/A')}")
                print(f"     Location: {job.get('location', 'N/A')}")
                print(f"     URL: {job.get('url', 'N/A')[:80]}...")
                print()
            await client.close()
            return True
        else:
            print("[WARNING] No jobs returned")
            await client.close()
            return False
            
    except Exception as e:
        print(f"[ERROR] Adzuna API test failed: {e}")
        import traceback
        traceback.print_exc()
        await client.close()
        return False


async def test_jsearch_api():
    """Test JSearch API client."""
    print("=" * 60)
    print("Testing JSearch API")
    print("=" * 60)
    
    if not settings.jsearch_api_key:
        print("[SKIP] JSearch API key not configured")
        return False
    
    print(f"API Key: {'*' * 20}")
    print()
    
    client = JSearchAPIClient()
    
    try:
        print("Searching for 'Python developer' in 'Minneapolis, MN'...")
        jobs = await client.search_jobs("Python developer", "Minneapolis, MN", limit=5)
        
        if jobs:
            print(f"[SUCCESS] Found {len(jobs)} jobs")
            print()
            for i, job in enumerate(jobs[:3], 1):
                print(f"  {i}. {job.get('title', 'N/A')}")
                print(f"     Company: {job.get('company', 'N/A')}")
                print(f"     Location: {job.get('location', 'N/A')}")
                print(f"     URL: {job.get('url', 'N/A')[:80]}...")
                print()
            await client.close()
            return True
        else:
            print("[WARNING] No jobs returned")
            await client.close()
            return False
            
    except Exception as e:
        print(f"[ERROR] JSearch API test failed: {e}")
        import traceback
        traceback.print_exc()
        await client.close()
        return False


async def test_job_source_manager():
    """Test JobSourceManager with aggregator APIs."""
    print("=" * 60)
    print("Testing JobSourceManager with Aggregator APIs")
    print("=" * 60)
    
    manager = JobSourceManager()
    
    try:
        print("Checking API client availability...")
        print(f"  Adzuna: {'[OK] Available' if manager.has_api_client('adzuna') else '[SKIP] Not configured'}")
        print(f"  JSearch: {'[OK] Available' if manager.has_api_client('jsearch') else '[SKIP] Not configured'}")
        print()
        
        print("Searching via JobSourceManager...")
        print("  Sources: adzuna, jsearch")
        print("  Query: Python developer")
        print("  Location: Minneapolis, MN")
        print()
        
        jobs = await manager.search_jobs(
            query="Python developer",
            location="Minneapolis, MN",
            sources=["adzuna", "jsearch"],
            limit=10
        )
        
        if jobs:
            print(f"[SUCCESS] Found {len(jobs)} total jobs from aggregator APIs")
            print()
            
            # Group by source
            by_source = {}
            for job in jobs:
                source = job.get('source', 'unknown')
                by_source.setdefault(source, []).append(job)
            
            for source, source_jobs in by_source.items():
                print(f"  {source}: {len(source_jobs)} jobs")
            
            print()
            print("Sample jobs:")
            for i, job in enumerate(jobs[:5], 1):
                print(f"  {i}. [{job.get('source', 'unknown')}] {job.get('title', 'N/A')}")
                print(f"     {job.get('company', 'N/A')} - {job.get('location', 'N/A')}")
            
            await manager.close()
            return True
        else:
            print("[WARNING] No jobs returned from JobSourceManager")
            await manager.close()
            return False
            
    except Exception as e:
        print(f"[ERROR] JobSourceManager test failed: {e}")
        import traceback
        traceback.print_exc()
        await manager.close()
        return False


async def test_api_endpoint():
    """Test the API endpoint with aggregator sources."""
    print("=" * 60)
    print("Testing API Endpoint with Aggregator Sources")
    print("=" * 60)
    
    import httpx
    
    base_url = "http://localhost:8004"
    
    try:
        # Check if service is running
        try:
            response = httpx.get(f"{base_url}/health", timeout=5.0)
            if response.status_code != 200:
                print("[SKIP] Service is not running or not healthy")
                return False
        except httpx.ConnectError:
            print("[SKIP] Service is not running")
            print("  Start the service with: .\\start_service.ps1")
            return False
        
        print("Service is running. Testing /api/v1/jobs/search endpoint...")
        print()
        
        # Test search with aggregator sources
        search_data = {
            "query": "Python developer",
            "location": "Minneapolis, MN",
            "sources": ["adzuna", "jsearch"],
            "limit": 10,
            "min_match_score": 0.0
        }
        
        response = httpx.post(
            f"{base_url}/api/v1/jobs/search",
            json=search_data,
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            print(f"[SUCCESS] API returned {len(jobs)} jobs")
            print(f"  Sources searched: {data.get('sources_searched', [])}")
            print()
            
            if jobs:
                print("Sample jobs from API:")
                for i, job in enumerate(jobs[:5], 1):
                    print(f"  {i}. [{job.get('source', 'unknown')}] {job.get('title', 'N/A')}")
                    print(f"     {job.get('company', 'N/A')} - {job.get('location', 'N/A')}")
            
            return True
        else:
            print(f"[ERROR] API returned status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"[ERROR] API endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  AGGREGATOR API TESTING")
    print("=" * 60)
    print()
    
    results = {}
    
    # Test individual APIs
    results['adzuna'] = await test_adzuna_api()
    print()
    
    results['jsearch'] = await test_jsearch_api()
    print()
    
    # Test JobSourceManager
    results['manager'] = await test_job_source_manager()
    print()
    
    # Test API endpoint (if service is running)
    results['endpoint'] = await test_api_endpoint()
    print()
    
    # Summary
    print("=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {test_name.upper()}: {status}")
    
    print()
    
    if all(results.values()):
        print("[SUCCESS] All tests passed!")
        sys.exit(0)
    else:
        print("[WARNING] Some tests failed. Check output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

