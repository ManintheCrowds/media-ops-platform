#!/usr/bin/env python3
"""Test browser scraping for all sources to determine if it bypasses 403 errors."""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.browser_scraper import BrowserJobScraper
from app.services.job_api import (
    IndeedScraper,
    LinkedInScraper,
    GlassdoorScraper,
    ZipRecruiterScraper
)


async def test_browser_fetch(source_name: str, url: str) -> Dict:
    """Test browser scraper fetching a URL.
    
    Args:
        source_name: Name of the source
        url: URL to fetch
        
    Returns:
        Dictionary with test results
    """
    print(f"\n{'='*60}")
    print(f"Testing {source_name} with browser scraper")
    print(f"URL: {url}")
    print('='*60)
    
    scraper = BrowserJobScraper(source_name)
    result = {
        "source": source_name,
        "url": url,
        "success": False,
        "status_code": None,
        "html_length": 0,
        "error": None,
        "elapsed_time": 0.0,
        "has_job_content": False
    }
    
    start_time = time.time()
    
    try:
        html = await scraper._fetch_page(url, wait_timeout=30000)
        
        result["elapsed_time"] = time.time() - start_time
        
        if html:
            result["success"] = True
            result["html_length"] = len(html)
            result["status_code"] = 200
            
            # Check if HTML contains job-related content
            html_lower = html.lower()
            job_indicators = ["job", "position", "career", "apply", "hiring"]
            result["has_job_content"] = any(indicator in html_lower for indicator in job_indicators)
            
            print(f"✓ Success! Fetched {len(html)} bytes")
            print(f"  Time: {result['elapsed_time']:.2f}s")
            print(f"  Has job content: {result['has_job_content']}")
            
            # Show snippet
            if len(html) > 0:
                snippet = html[:200].replace('\n', ' ').replace('\r', ' ')
                print(f"  HTML snippet: {snippet}...")
        else:
            result["error"] = "No HTML returned"
            print(f"✗ Failed: No HTML returned")
            
    except Exception as e:
        result["elapsed_time"] = time.time() - start_time
        result["error"] = str(e)
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()
    
    return result


async def test_browser_search(source_name: str, query: str, location: str) -> Dict:
    """Test browser scraper searching for jobs.
    
    Args:
        source_name: Name of the source
        query: Search query
        location: Location string
        
    Returns:
        Dictionary with test results
    """
    print(f"\n{'='*60}")
    print(f"Testing {source_name} browser search")
    print(f"Query: '{query}' in '{location}'")
    print('='*60)
    
    # Get the HTTP scraper to use its search logic
    scrapers = {
        "indeed": IndeedScraper,
        "linkedin": LinkedInScraper,
        "glassdoor": GlassdoorScraper,
        "ziprecruiter": ZipRecruiterScraper,
    }
    
    if source_name not in scrapers:
        return {
            "source": source_name,
            "success": False,
            "error": f"Unknown source: {source_name}",
            "jobs_found": 0
        }
    
    http_scraper = scrapers[source_name]()
    browser_scraper = BrowserJobScraper(source_name)
    
    result = {
        "source": source_name,
        "query": query,
        "location": location,
        "success": False,
        "jobs_found": 0,
        "error": None,
        "elapsed_time": 0.0
    }
    
    start_time = time.time()
    
    try:
        # Replace HTTP scraper's _fetch_page with browser version
        original_fetch = http_scraper._fetch_page
        
        async def browser_fetch(url, **kwargs):
            html = await browser_scraper._fetch_page(url, **kwargs)
            if html:
                # Create a mock response object
                class MockResponse:
                    def __init__(self, text):
                        self.text = text
                        self.status_code = 200
                        self.cookies = {}
                        self.headers = {}
                return MockResponse(html)
            return None
        
        http_scraper._fetch_page = browser_fetch
        
        try:
            jobs = await http_scraper.search_jobs(query, location, limit=5)
            
            result["elapsed_time"] = time.time() - start_time
            result["jobs_found"] = len(jobs)
            result["success"] = len(jobs) > 0
            
            if result["success"]:
                print(f"✓ Success! Found {len(jobs)} jobs")
                print(f"  Time: {result['elapsed_time']:.2f}s")
                
                for i, job in enumerate(jobs[:3], 1):
                    print(f"  {i}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
            else:
                print(f"✗ No jobs found")
                result["error"] = "No jobs returned"
                
        finally:
            # Restore original fetch method
            http_scraper._fetch_page = original_fetch
            
    except Exception as e:
        result["elapsed_time"] = time.time() - start_time
        result["error"] = str(e)
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await http_scraper.close()
        await browser_scraper.close()
    
    return result


async def main():
    """Run all browser scraping tests."""
    print("="*60)
    print("  BROWSER SCRAPING TEST SUITE")
    print("="*60)
    print("\nThis script tests if browser scraping bypasses 403 errors")
    print("for job sites that block HTTP scrapers.\n")
    
    # Test URLs for each source
    test_urls = {
        "indeed": "https://www.indeed.com/jobs?q=Python+developer&l=Minneapolis%2C+MN",
        "linkedin": "https://www.linkedin.com/jobs/search?keywords=Python%20developer&location=Minneapolis%2C%20MN",
        "glassdoor": "https://www.glassdoor.com/Job/jobs.htm?sc.keyword=Python+developer&locT=C&locId=Minneapolis%2C+MN",
        "ziprecruiter": "https://www.ziprecruiter.com/jobs/search?search=Python+developer&location=Minneapolis%2C+MN"
    }
    
    fetch_results = []
    search_results = []
    
    # Test 1: Simple page fetch
    print("\n" + "="*60)
    print("  PHASE 1: Testing Browser Page Fetch")
    print("="*60)
    
    for source, url in test_urls.items():
        result = await test_browser_fetch(source, url)
        fetch_results.append(result)
        await asyncio.sleep(3)  # Rate limiting
    
    # Test 2: Full job search
    print("\n" + "="*60)
    print("  PHASE 2: Testing Browser Job Search")
    print("="*60)
    
    for source in ["indeed", "glassdoor", "ziprecruiter"]:  # Skip LinkedIn for now
        result = await test_browser_search(source, "Python developer", "Minneapolis, MN")
        search_results.append(result)
        await asyncio.sleep(5)  # Rate limiting
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    print("\nPage Fetch Results:")
    for result in fetch_results:
        status = "✓" if result["success"] else "✗"
        print(f"  {status} {result['source']:15} - "
              f"Success: {result['success']}, "
              f"HTML: {result['html_length']} bytes, "
              f"Time: {result['elapsed_time']:.2f}s")
        if result["error"]:
            print(f"      Error: {result['error']}")
    
    print("\nJob Search Results:")
    for result in search_results:
        status = "✓" if result["success"] else "✗"
        print(f"  {status} {result['source']:15} - "
              f"Jobs: {result['jobs_found']}, "
              f"Time: {result['elapsed_time']:.2f}s")
        if result["error"]:
            print(f"      Error: {result['error']}")
    
    # Success rate
    fetch_success = sum(1 for r in fetch_results if r["success"])
    search_success = sum(1 for r in search_results if r["success"])
    
    print(f"\nSuccess Rates:")
    print(f"  Page Fetch: {fetch_success}/{len(fetch_results)} ({fetch_success/len(fetch_results)*100:.1f}%)")
    print(f"  Job Search: {search_success}/{len(search_results)} ({search_success/len(search_results)*100:.1f}%)")
    
    print("\n" + "="*60)
    print("  RECOMMENDATIONS")
    print("="*60)
    
    if fetch_success == len(fetch_results):
        print("✓ Browser scraping successfully bypasses 403 errors!")
        print("  → Update JobSourceManager to prioritize browser scraping")
        print("  → Remove xfail markers from tests")
    elif fetch_success > 0:
        print("⚠ Browser scraping works for some sources")
        print("  → Document which sources work")
        print("  → Use browser scraping as fallback for working sources")
    else:
        print("✗ Browser scraping still blocked")
        print("  → Need to enhance stealth mode")
        print("  → Consider proxy rotation")
        print("  → Document limitations")


if __name__ == "__main__":
    asyncio.run(main())

