"""Scan for jobs and display them in a list."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from app.services.job_source_manager import JobSourceManager

async def scan_and_list_jobs(
    query: str = "python developer",
    location: str = "Minneapolis, MN",
    sources: list = None,
    limit: int = 50
):
    """Scan for jobs and display them."""
    if sources is None:
        sources = ["adzuna", "indeed"]
    
    print("=" * 80)
    print("JOB SCAN SYSTEM")
    print("=" * 80)
    print(f"Query: {query}")
    print(f"Location: {location}")
    print(f"Sources: {', '.join(sources)}")
    print(f"Limit: {limit}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    manager = JobSourceManager()
    
    try:
        print("Scanning for jobs...")
        jobs = await manager.search_jobs(
            query=query,
            location=location,
            sources=sources,
            limit=limit
        )
        
        print(f"\nFound {len(jobs)} jobs\n")
        
        if not jobs:
            print("[WARNING] No jobs found")
            return
        
        # Display jobs
        print("=" * 80)
        print("JOB LISTING")
        print("=" * 80)
        print()
        
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job.get('title', 'N/A')}")
            print(f"   Company: {job.get('company', 'N/A')}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Source: {job.get('source', 'N/A')}")
            
            # Match scores
            skill_score = job.get('skill_match_score', 0.0)
            exp_score = job.get('experience_match_score', 0.0)
            overall_score = job.get('overall_match_score', 0.0)
            
            if overall_score > 0:
                print(f"   Match Scores: Skill={skill_score:.2f}, Exp={exp_score:.2f}, Overall={overall_score:.2f}")
            
            # Additional info
            if job.get('salary_range'):
                print(f"   Salary: {job.get('salary_range')}")
            if job.get('job_type'):
                print(f"   Type: {job.get('job_type')}")
            if job.get('remote'):
                print(f"   Remote: Yes")
            
            print(f"   URL: {job.get('url', 'N/A')}")
            print()
        
        # Summary by source
        print("=" * 80)
        print("SUMMARY BY SOURCE")
        print("=" * 80)
        from collections import Counter
        source_counts = Counter(j.get('source', 'unknown') for j in jobs)
        for source, count in source_counts.most_common():
            print(f"  {source}: {count} jobs")
        print()
        
        # Save to JSON
        output_file = Path(__file__).parent / "jobs_scan_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "scan_time": datetime.now().isoformat(),
                "query": query,
                "location": location,
                "sources": sources,
                "total_jobs": len(jobs),
                "jobs": jobs
            }, f, indent=2, default=str)
        
        print(f"[OK] Results saved to: {output_file}")
        
    except Exception as e:
        print(f"[ERROR] Failed to scan jobs: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await manager.close()

if __name__ == "__main__":
    import sys
    
    # Default values
    query = "python developer"
    location = "Minneapolis, MN"
    sources = ["adzuna", "indeed"]
    limit = 50
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        query = sys.argv[1]
    if len(sys.argv) > 2:
        location = sys.argv[2]
    if len(sys.argv) > 3:
        sources = sys.argv[3].split(",")
    if len(sys.argv) > 4:
        limit = int(sys.argv[4])
    
    asyncio.run(scan_and_list_jobs(query, location, sources, limit))

