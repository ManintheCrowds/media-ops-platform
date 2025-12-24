"""Query and analyze stored jobs from the database."""

import httpx
import json
import sys
from typing import Dict, List, Optional
from collections import defaultdict

BASE_URL = "http://localhost:8004"

def check_service() -> bool:
    """Check if the service is running."""
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False

def get_all_jobs(limit: int = 100, offset: int = 0) -> List[Dict]:
    """Get all jobs from the API with pagination."""
    all_jobs = []
    current_offset = offset
    page_size = min(limit, 100)  # API max is 100
    
    while True:
        try:
            response = httpx.get(
                f"{BASE_URL}/api/v1/jobs",
                params={"limit": page_size, "offset": current_offset, "active_only": False},
                timeout=30.0
            )
            if response.status_code == 200:
                jobs = response.json()
                if not jobs:
                    break
                all_jobs.extend(jobs)
                if len(jobs) < page_size:
                    break
                current_offset += page_size
                if len(all_jobs) >= limit:
                    break
            else:
                print(f"Error: {response.status_code} - {response.text}")
                break
        except Exception as e:
            print(f"Error fetching jobs: {e}")
            break
    
    return all_jobs

def get_jobs_by_source(source: str) -> List[Dict]:
    """Get jobs filtered by source."""
    try:
        response = httpx.get(
            f"{BASE_URL}/api/v1/jobs",
            params={"source": source, "limit": 1000, "active_only": False},
            timeout=30.0
        )
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception:
        return []

def get_recommended_jobs(min_score: float = 0.7) -> List[Dict]:
    """Get recommended jobs."""
    try:
        response = httpx.get(
            f"{BASE_URL}/api/v1/jobs/recommended",
            params={"min_score": min_score, "limit": 100},
            timeout=30.0
        )
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception:
        return []

def analyze_jobs(jobs: List[Dict]) -> Dict:
    """Analyze jobs and return statistics."""
    stats = {
        "total": len(jobs),
        "by_source": defaultdict(int),
        "by_match_score": {
            "high": 0,  # >= 0.7
            "medium": 0,  # 0.4 - 0.69
            "low": 0,  # < 0.4
            "none": 0  # null or 0
        },
        "with_description": 0,
        "with_salary": 0,
        "remote": 0,
        "sources": set(),
        "companies": set(),
        "locations": set(),
    }
    
    for job in jobs:
        # Source breakdown
        source = job.get("source", "unknown")
        stats["by_source"][source] += 1
        stats["sources"].add(source)
        
        # Match score breakdown
        score = job.get("overall_match_score")
        if score is None or score == 0:
            stats["by_match_score"]["none"] += 1
        elif score >= 0.7:
            stats["by_match_score"]["high"] += 1
        elif score >= 0.4:
            stats["by_match_score"]["medium"] += 1
        else:
            stats["by_match_score"]["low"] += 1
        
        # Other fields
        if job.get("description"):
            stats["with_description"] += 1
        if job.get("salary_range"):
            stats["with_salary"] += 1
        if job.get("remote"):
            stats["remote"] += 1
        
        # Unique values
        if job.get("company"):
            stats["companies"].add(job["company"])
        if job.get("location"):
            stats["locations"].add(job["location"])
    
    # Convert sets to counts
    stats["unique_companies"] = len(stats["companies"])
    stats["unique_locations"] = len(stats["locations"])
    stats["unique_sources"] = len(stats["sources"])
    stats["sources"] = list(stats["sources"])
    
    return stats

def print_statistics(stats: Dict, jobs: List[Dict]):
    """Print formatted statistics."""
    print("=" * 60)
    print("JOBS INVENTORY STATISTICS")
    print("=" * 60)
    print()
    
    print(f"Total Jobs: {stats['total']}")
    print()
    
    print("By Source:")
    for source, count in sorted(stats["by_source"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")
    print()
    
    print("By Match Score:")
    print(f"  High (>= 0.7): {stats['by_match_score']['high']}")
    print(f"  Medium (0.4-0.69): {stats['by_match_score']['medium']}")
    print(f"  Low (< 0.4): {stats['by_match_score']['low']}")
    print(f"  None/Zero: {stats['by_match_score']['none']}")
    print()
    
    print("Data Completeness:")
    print(f"  With Description: {stats['with_description']} ({stats['with_description']/max(stats['total'],1)*100:.1f}%)")
    print(f"  With Salary: {stats['with_salary']} ({stats['with_salary']/max(stats['total'],1)*100:.1f}%)")
    print(f"  Remote Jobs: {stats['remote']} ({stats['remote']/max(stats['total'],1)*100:.1f}%)")
    print()
    
    print("Unique Values:")
    print(f"  Companies: {stats['unique_companies']}")
    print(f"  Locations: {stats['unique_locations']}")
    print(f"  Sources: {stats['unique_sources']}")
    print()
    
    if jobs:
        print("Sample Jobs (Top 5 by Match Score):")
        sorted_jobs = sorted(
            [j for j in jobs if j.get("overall_match_score")],
            key=lambda x: x.get("overall_match_score", 0),
            reverse=True
        )[:5]
        
        for i, job in enumerate(sorted_jobs, 1):
            print(f"  {i}. {job.get('title', 'N/A')}")
            print(f"     Company: {job.get('company', 'N/A')}")
            print(f"     Location: {job.get('location', 'N/A')}")
            print(f"     Source: {job.get('source', 'N/A')}")
            print(f"     Match Score: {job.get('overall_match_score', 0):.2f}")
            print(f"     URL: {job.get('url', 'N/A')[:80]}...")
            print()

def main():
    """Main function."""
    print("Querying Jobs from Database...")
    print()
    
    if not check_service():
        print("[ERROR] Service is not running!")
        print("  Start with: .\\start_service.ps1")
        sys.exit(1)
    
    # Get all jobs
    print("Fetching all jobs (with pagination)...")
    all_jobs = get_all_jobs(limit=1000)  # Fetch up to 1000 jobs
    
    if not all_jobs:
        print("[WARNING] No jobs found in database")
        print("  This could mean:")
        print("  - No searches have been successfully completed")
        print("  - Database commit is failing (known issue)")
        print("  - Jobs are being filtered out")
        return
    
    # Analyze
    stats = analyze_jobs(all_jobs)
    print_statistics(stats, all_jobs)
    
    # Get jobs by source
    print("=" * 60)
    print("JOBS BY SOURCE")
    print("=" * 60)
    print()
    
    for source in stats["sources"]:
        source_jobs = get_jobs_by_source(source)
        print(f"{source}: {len(source_jobs)} jobs")
    
    print()
    
    # Get recommended jobs
    print("=" * 60)
    print("RECOMMENDED JOBS (Score >= 0.7)")
    print("=" * 60)
    print()
    
    recommended = get_recommended_jobs(min_score=0.7)
    print(f"Found {len(recommended)} recommended jobs")
    
    if recommended:
        print("\nTop Recommended Jobs:")
        for i, job in enumerate(recommended[:10], 1):
            print(f"  {i}. {job.get('title', 'N/A')} - {job.get('company', 'N/A')}")
            print(f"     Score: {job.get('overall_match_score', 0):.2f}")
    
    # Export to JSON
    export_data = {
        "statistics": stats,
        "total_jobs": len(all_jobs),
        "sample_jobs": all_jobs[:10] if all_jobs else []
    }
    
    with open("jobs_inventory.json", "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, default=str)
    
    print()
    print(f"[OK] Exported data to jobs_inventory.json")

if __name__ == "__main__":
    main()

