#!/usr/bin/env python3
"""Standalone script to test job search with real queries and detailed output."""

import asyncio
import httpx
import json
import time
from typing import Dict, List
from pathlib import Path

BASE_URL = "http://localhost:8004"
import os
import tempfile
DEBUG_LOG_PATH = Path(
    os.environ.get("TEST_DEBUG_LOG", str(Path(tempfile.gettempdir()) / "job_automation_test_debug.log"))
)


def write_debug_log(session_id: str, run_id: str, hypothesis_id: str, location: str, message: str, data: Dict):
    """Write debug log entry."""
    try:
        log_entry = {
            "sessionId": session_id,
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000)
        }
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass


async def test_scraper_directly(scraper_name: str, query: str, location: str):
    """Test a scraper directly."""
    print(f"\n{'='*60}")
    print(f"Testing {scraper_name} scraper directly")
    print('='*60)
    
    from app.services.job_api import (
        IndeedScraper,
        LinkedInScraper,
        GlassdoorScraper,
        ZipRecruiterScraper
    )
    
    scrapers = {
        "indeed": IndeedScraper,
        "linkedin": LinkedInScraper,
        "glassdoor": GlassdoorScraper,
        "ziprecruiter": ZipRecruiterScraper,
    }
    
    if scraper_name not in scrapers:
        print(f"Unknown scraper: {scraper_name}")
        return
    
    scraper = scrapers[scraper_name]()
    start_time = time.time()
    
    try:
        print(f"Searching for: '{query}' in '{location}'")
        jobs = await scraper.search_jobs(query=query, location=location, limit=5)
        
        elapsed = time.time() - start_time
        
        print(f"\nResults:")
        print(f"  Jobs found: {len(jobs)}")
        print(f"  Time taken: {elapsed:.2f}s")
        
        if len(jobs) > 0:
            print(f"\n  Sample jobs:")
            for i, job in enumerate(jobs[:3], 1):
                print(f"    {i}. {job.get('title', 'N/A')}")
                print(f"       Company: {job.get('company', 'N/A')}")
                print(f"       Location: {job.get('location', 'N/A')}")
                print(f"       URL: {job.get('url', 'N/A')[:80]}...")
                print(f"       Has description: {bool(job.get('description'))}")
                if job.get('description'):
                    desc_preview = job['description'][:100].replace('\n', ' ')
                    print(f"       Description preview: {desc_preview}...")
                print()
        else:
            print("  [WARNING] No jobs found - scraper may be blocked or site structure changed")
            
    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()


async def test_api_endpoint(query: str, location: str, sources: List[str] = None):
    """Test the API endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing API endpoint: /api/v1/jobs/search")
    print('='*60)
    
    payload = {
        "query": query,
        "location": location,
        "limit": 10,
        "min_match_score": 0.0  # Accept all for testing
    }
    
    if sources:
        payload["sources"] = sources
    
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/jobs/search",
                json=payload
            )
            
            elapsed = time.time() - start_time
            
            print(f"Status: {response.status_code}")
            print(f"Time taken: {elapsed:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\nResults:")
                print(f"  Total jobs found: {data.get('count', 0)}")
                print(f"  Sources searched: {', '.join(data.get('sources_searched', []))}")
                
                jobs = data.get('jobs', [])
                
                if len(jobs) > 0:
                    print(f"\n  Job details:")
                    for i, job in enumerate(jobs[:5], 1):
                        print(f"    {i}. {job.get('title', 'N/A')}")
                        print(f"       Company: {job.get('company', 'N/A')}")
                        print(f"       Match score: {job.get('overall_match_score', 0):.2f}")
                        print(f"       URL: {job.get('url', 'N/A')[:80]}...")
                        print()
                else:
                    print("  [WARNING] No jobs returned")
            else:
                print(f"  [ERROR] Error: {response.text}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()


async def test_database_storage():
    """Test that jobs are stored in database."""
    print(f"\n{'='*60}")
    print(f"Testing database storage")
    print('='*60)
    
    # First, run a search
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/jobs/search",
            json={
                "query": "Python developer",
                "location": "Minneapolis, MN",
                "limit": 5,
                "min_match_score": 0.0
            }
        )
        
        if response.status_code != 200:
            print(f"[ERROR] Search failed: {response.status_code}")
            return
        
        data = response.json()
        job_count = data.get('count', 0)
        
        print(f"Jobs found in search: {job_count}")
        
        # Now check database
        db_response = await client.get(
            f"{BASE_URL}/api/v1/jobs",
            params={"limit": 100}
        )
        
        if db_response.status_code == 200:
            db_jobs = db_response.json()
            print(f"Jobs in database: {len(db_jobs)}")
            
            if len(db_jobs) > 0:
                print(f"\n  Sample database jobs:")
                for i, job in enumerate(db_jobs[:3], 1):
                    print(f"    {i}. {job.get('title', 'N/A')} (ID: {job.get('id')})")
                    print(f"       Source: {job.get('source', 'N/A')}")
                    print(f"       Score: {job.get('overall_match_score', 0):.2f}")
        else:
            print(f"[ERROR] Failed to query database: {db_response.status_code}")


async def main():
    """Run all tests."""
    import sys
    
    # Clear previous log file
    try:
        if DEBUG_LOG_PATH.exists():
            DEBUG_LOG_PATH.unlink()
    except Exception:
        pass
    
    session_id = "real-world-test"
    run_id = f"run-{int(time.time())}"
    
    write_debug_log(session_id, run_id, "H0", "test_job_search_real.py:main", "Starting real-world job search tests", {})
    
    print("="*60)
    print("  REAL-WORLD JOB SEARCH TESTING")
    print("="*60)
    
    # Test 1: Direct scraper tests (all sources)
    print("\n" + "="*60)
    print("  TESTING ALL SCRAPERS DIRECTLY")
    print("="*60)
    
    for source in ["indeed", "glassdoor", "ziprecruiter"]:
        await test_scraper_directly(source, "Python developer", "Minneapolis, MN")
        await asyncio.sleep(2)  # Rate limiting between sources
    
    # Test 2: API endpoint test with all sources
    await test_api_endpoint("Python developer", "Minneapolis, MN", sources=["indeed", "glassdoor", "ziprecruiter"])
    
    # Test 3: Database storage test
    await test_database_storage()
    
    print(f"\n{'='*60}")
    print("  TESTING COMPLETE")
    print('='*60)
    print(f"\nDebug logs written to: {DEBUG_LOG_PATH}")
    print("\nNext steps:")
    print("  1. Check debug logs for detailed web access information")
    print("  2. Review job data quality")
    print("  3. Verify URLs are accessible")
    print("  4. Check database for stored jobs")


if __name__ == "__main__":
    asyncio.run(main())

