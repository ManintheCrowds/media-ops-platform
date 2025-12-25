"""Test LinkedIn, Glassdoor, and ZipRecruiter sources to determine which work vs blocked."""

import asyncio
import httpx
import sys
import json
from pathlib import Path
from typing import Dict, List

BASE_URL = "http://localhost:8004"
LOG_PATH = Path(r"d:\CodeRepositories\.cursor\debug.log")

def log_entry(session_id, run_id, hypothesis_id, location, message, data):
    """Write debug log entry."""
    entry = {
        "sessionId": session_id,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(__import__('time').time() * 1000)
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

async def check_server_health():
    """Check if the API server is running."""
    # #region agent log
    log_entry("test-sources", "run1", "H-SERVER", "test_other_sources.py:check_server_health", "Checking server health", {
        "base_url": BASE_URL
    })
    # #endregion agent log
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/health")
            # #region agent log
            log_entry("test-sources", "run1", "H-SERVER", "test_other_sources.py:check_server_health", "Server health check result", {
                "status_code": response.status_code,
                "server_running": response.status_code == 200
            })
            # #endregion agent log
            return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        # #region agent log
        log_entry("test-sources", "run1", "H-SERVER", "test_other_sources.py:check_server_health", "Server not reachable", {
            "error": str(e),
            "error_type": type(e).__name__,
            "server_running": False
        })
        # #endregion agent log
        return False
    except Exception as e:
        # #region agent log
        log_entry("test-sources", "run1", "H-SERVER", "test_other_sources.py:check_server_health", "Unexpected error checking server", {
            "error": str(e),
            "error_type": type(e).__name__
        })
        # #endregion agent log
        return False

async def test_source_via_api(source: str, query: str = "Python developer", location: str = "Minneapolis, MN") -> Dict:
    """Test a source via the API endpoint.
    
    Returns:
        Dict with test results
    """
    print(f"\n{'='*60}")
    print(f"Testing source: {source.upper()}")
    print('='*60)
    
    result = {
        "source": source,
        "status": "unknown",
        "jobs_found": 0,
        "error": None,
        "response_time": 0.0
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            import time
            start_time = time.time()
            
            # #region agent log
            log_entry("test-sources", "run1", "H-API-CALL", "test_other_sources.py:test_source_via_api", f"Calling API for {source}", {
                "source": source,
                "url": f"{BASE_URL}/api/v1/jobs/search",
                "query": query,
                "location": location
            })
            # #endregion agent log
            
            response = await client.post(
                f"{BASE_URL}/api/v1/jobs/search",
                json={
                    "query": query,
                    "location": location,
                    "sources": [source],
                    "limit": 5,
                    "min_match_score": 0.0
                }
            )
            
            elapsed = time.time() - start_time
            result["response_time"] = elapsed
            
            if response.status_code == 200:
                data = response.json()
                jobs_count = data.get('count', 0)
                sources_searched = data.get('sources_searched', [])
                
                result["jobs_found"] = jobs_count
                
                if source in sources_searched:
                    if jobs_count > 0:
                        result["status"] = "working"
                        print(f"✅ {source.upper()}: WORKING - Found {jobs_count} jobs")
                        print(f"   Response time: {elapsed:.2f}s")
                        
                        # Show sample jobs
                        jobs = data.get('jobs', [])
                        if jobs:
                            print(f"   Sample jobs:")
                            for i, job in enumerate(jobs[:3], 1):
                                print(f"      {i}. {job.get('title')} at {job.get('company')}")
                    else:
                        result["status"] = "no_results"
                        print(f"⚠️  {source.upper()}: NO RESULTS - Search completed but no jobs found")
                        print(f"   Response time: {elapsed:.2f}s")
                        print(f"   This could mean:")
                        print(f"      - Source is working but no jobs match the query")
                        print(f"      - Source is blocked but returns empty results")
                else:
                    result["status"] = "not_searched"
                    print(f"❌ {source.upper()}: NOT SEARCHED - Source was not included in search")
                    print(f"   Sources searched: {sources_searched}")
            else:
                result["status"] = "api_error"
                result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
                print(f"❌ {source.upper()}: API ERROR - {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                
        except httpx.ConnectError as e:
            result["status"] = "server_down"
            result["error"] = "Cannot connect to server - server may not be running"
            print(f"❌ {source.upper()}: SERVER NOT RUNNING - Cannot connect to {BASE_URL}")
            print(f"   Start the server with: cd d:\\software\\job-automation-service && .\\restart_server.ps1")
            # #region agent log
            log_entry("test-sources", "run1", "H-CONNECTION", "test_other_sources.py:test_source_via_api", f"Connection error for {source}", {
                "source": source,
                "error": str(e),
                "error_type": "ConnectError",
                "server_running": False
            })
            # #endregion agent log
        except httpx.TimeoutException:
            result["status"] = "timeout"
            result["error"] = "Request timeout"
            print(f"❌ {source.upper()}: TIMEOUT - Request took too long")
            # #region agent log
            log_entry("test-sources", "run1", "H-TIMEOUT", "test_other_sources.py:test_source_via_api", f"Timeout for {source}", {
                "source": source
            })
            # #endregion agent log
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"❌ {source.upper()}: ERROR - {e}")
            # #region agent log
            log_entry("test-sources", "run1", "H-ERROR", "test_other_sources.py:test_source_via_api", f"Error for {source}", {
                "source": source,
                "error": str(e),
                "error_type": type(e).__name__
            })
            # #endregion agent log
            import traceback
            traceback.print_exc()
    
    return result


async def test_all_sources():
    """Test all sources and generate a summary report."""
    print("="*80)
    print("TESTING ALL JOB SOURCES")
    print("="*80)
    print()
    print("This will test LinkedIn, Glassdoor, and ZipRecruiter sources")
    print("to determine which are working vs blocked.")
    print()
    
    # #region agent log
    log_entry("test-sources", "run1", "H0", "test_other_sources.py:test_all_sources", "Starting source tests", {
        "base_url": BASE_URL
    })
    # #endregion agent log
    
    # Check if server is running first
    print("Checking if API server is running...")
    server_running = await check_server_health()
    
    if not server_running:
        print()
        print("="*80)
        print("ERROR: API SERVER IS NOT RUNNING")
        print("="*80)
        print()
        print(f"Cannot connect to {BASE_URL}")
        print()
        print("To start the server:")
        print("  1. Open a new PowerShell window")
        print("  2. Run: cd d:\\software\\job-automation-service")
        print("  3. Run: .\\restart_server.ps1")
        print()
        print("Or manually:")
        print("  $env:DATABASE_URL = 'postgresql://jobautomation:password@localhost:5433/jobautomation'")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8004")
        print()
        return []
    
    print("Server is running. Proceeding with tests...")
    print()
    
    sources_to_test = ["linkedin", "glassdoor", "ziprecruiter"]
    results = []
    
    for source in sources_to_test:
        result = await test_source_via_api(source)
        results.append(result)
        # Rate limiting between tests
        await asyncio.sleep(2)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    print()
    
    working = [r for r in results if r["status"] == "working"]
    no_results = [r for r in results if r["status"] == "no_results"]
    blocked = [r for r in results if r["status"] in ["not_searched", "api_error", "timeout", "error"]]
    
    if working:
        print("✅ WORKING SOURCES:")
        for r in working:
            print(f"   - {r['source'].upper()}: {r['jobs_found']} jobs found ({r['response_time']:.2f}s)")
        print()
    
    if no_results:
        print("⚠️  NO RESULTS (may be blocked or no matching jobs):")
        for r in no_results:
            print(f"   - {r['source'].upper()}: {r.get('error', 'No jobs found')}")
        print()
    
    if blocked:
        print("❌ BLOCKED/ERROR SOURCES:")
        for r in blocked:
            error_msg = r.get('error', 'Unknown error')
            print(f"   - {r['source'].upper()}: {r['status']} - {error_msg}")
        print()
    
    # Recommendations
    print("="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    print()
    
    if working:
        print(f"✅ Use these sources: {', '.join([r['source'].upper() for r in working])}")
        print()
    
    if blocked or no_results:
        print("⚠️  For blocked sources, consider:")
        print("   1. Using official APIs if available")
        print("   2. Implementing browser scraping (Selenium/Playwright)")
        print("   3. Using proxy rotation")
        print("   4. Adding delays and better headers")
        print()
    
    return results


if __name__ == "__main__":
    print()
    results = asyncio.run(test_all_sources())
    print("="*80)
    print("TESTING COMPLETE")
    print("="*80)
    
    # Exit with error code if all sources failed
    working_count = len([r for r in results if r["status"] == "working"])
    sys.exit(0 if working_count > 0 else 1)


