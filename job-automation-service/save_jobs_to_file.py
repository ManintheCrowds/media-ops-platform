"""Save job search results to a text file."""

import requests
import json
from datetime import datetime
from pathlib import Path

BASE_URL = "http://localhost:8004"
OUTPUT_FILE = Path(__file__).parent / "jobs_output.txt"

def save_jobs_to_file(query: str = "python", location: str = "Minneapolis, MN", sources: list = None, limit: int = 25):
    """Search for jobs and save results to a text file."""
    if sources is None:
        sources = ["adzuna"]
    
    print(f"Searching for jobs: '{query}' in {location}")
    print(f"Sources: {', '.join(sources)}")
    print(f"Limit: {limit}")
    print()
    
    payload = {
        "query": query,
        "location": location,
        "limit": limit,
        "sources": sources
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/jobs/search",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        jobs = data.get("jobs", [])
        count = data.get("count", 0)
        sources_searched = data.get("sources_searched", [])
        
        print(f"Found {count} jobs")
        print(f"Sources searched: {', '.join(sources_searched)}")
        print(f"Saving to: {OUTPUT_FILE}")
        print()
        
        # Write to file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(f"JOB SEARCH RESULTS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Search Query: {query}\n")
            f.write(f"Location: {location}\n")
            f.write(f"Sources: {', '.join(sources_searched)}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Jobs Found: {count}\n")
            f.write("=" * 80 + "\n\n")
            
            if count == 0:
                f.write("No jobs found.\n")
            else:
                for idx, job in enumerate(jobs, 1):
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"JOB #{idx}\n")
                    f.write(f"{'=' * 80}\n")
                    f.write(f"Title: {job.get('title', 'N/A')}\n")
                    f.write(f"Company: {job.get('company', 'N/A')}\n")
                    f.write(f"Location: {job.get('location', 'N/A')}\n")
                    f.write(f"Source: {job.get('source', 'N/A')}\n")
                    f.write(f"URL: {job.get('url', 'N/A')}\n")
                    f.write(f"\nMatch Scores:\n")
                    f.write(f"  Skill Match: {job.get('skill_match_score', 0.0):.3f}\n")
                    f.write(f"  Experience Match: {job.get('experience_match_score', 0.0):.3f}\n")
                    f.write(f"  Overall Match: {job.get('overall_match_score', 0.0):.3f}\n")
                    
                    if job.get('description'):
                        f.write(f"\nDescription:\n{job.get('description', '')}\n")
                    
                    if job.get('requirements'):
                        f.write(f"\nRequirements:\n{job.get('requirements', '')}\n")
                    
                    if job.get('salary_range'):
                        f.write(f"\nSalary Range: {job.get('salary_range')}\n")
                    
                    if job.get('job_type'):
                        f.write(f"Job Type: {job.get('job_type')}\n")
                    
                    f.write(f"Remote: {'Yes' if job.get('remote', False) else 'No'}\n")
                    f.write(f"\n")
        
        print(f"[OK] Jobs saved to: {OUTPUT_FILE}")
        print(f"   File size: {OUTPUT_FILE.stat().st_size:,} bytes")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error calling API: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error saving jobs: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    # Default search
    query = "python"
    location = "Minneapolis, MN"
    sources = ["adzuna"]
    limit = 25
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        query = sys.argv[1]
    if len(sys.argv) > 2:
        location = sys.argv[2]
    if len(sys.argv) > 3:
        sources = sys.argv[3].split(",")
    if len(sys.argv) > 4:
        limit = int(sys.argv[4])
    
    success = save_jobs_to_file(query, location, sources, limit)
    sys.exit(0 if success else 1)

