"""Generate system status summary for evaluation."""

import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import httpx
import sys

sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.models.job_listing import JobListing

def get_system_status():
    """Get comprehensive system status."""
    status = {
        "timestamp": datetime.now().isoformat(),
        "database": {},
        "api_credentials": {},
        "api_server": {},
        "jobs": {},
        "recommendations": []
    }
    
    # Database status
    try:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        total_jobs = db.query(JobListing).count()
        adzuna_jobs = db.query(JobListing).filter(JobListing.source == "adzuna").count()
        jobs_with_source = db.query(JobListing).filter(JobListing.source != None, JobListing.source != "").count()
        jobs_with_scores = db.query(JobListing).filter(JobListing.overall_match_score > 0).count()
        
        status["database"] = {
            "connected": True,
            "total_jobs": total_jobs,
            "adzuna_jobs": adzuna_jobs,
            "jobs_with_source": jobs_with_source,
            "jobs_with_scores": jobs_with_scores,
            "legacy_jobs": total_jobs - jobs_with_source
        }
        
        db.close()
    except Exception as e:
        status["database"] = {"connected": False, "error": str(e)}
    
    # API Credentials
    status["api_credentials"] = {
        "adzuna_api_id": bool(settings.adzuna_api_id),
        "adzuna_api_key": bool(settings.adzuna_api_key),
        "jsearch_api_key": bool(settings.jsearch_api_key),
        "all_configured": all([
            settings.adzuna_api_id,
            settings.adzuna_api_key,
            settings.jsearch_api_key
        ])
    }
    
    # API Server
    try:
        response = httpx.get("http://localhost:8004/health", timeout=5.0)
        status["api_server"] = {
            "running": True,
            "status_code": response.status_code,
            "healthy": response.status_code == 200
        }
    except Exception as e:
        status["api_server"] = {"running": False, "error": str(e)}
    
    # Test job search
    if status["api_server"].get("running"):
        try:
            body = {
                "query": "python",
                "location": "Minneapolis, MN",
                "limit": 5,
                "sources": ["adzuna"]
            }
            response = httpx.post(
                "http://localhost:8004/api/v1/jobs/search",
                json=body,
                timeout=30.0
            )
            if response.status_code == 200:
                data = response.json()
                status["jobs"] = {
                    "search_works": True,
                    "jobs_returned": data.get("count", 0),
                    "sources_searched": data.get("sources_searched", [])
                }
            else:
                status["jobs"] = {
                    "search_works": False,
                    "error": f"Status {response.status_code}"
                }
        except Exception as e:
            status["jobs"] = {"search_works": False, "error": str(e)}
    
    # Generate recommendations
    recommendations = []
    
    if not status["api_server"].get("running"):
        recommendations.append({
            "priority": "HIGH",
            "action": "Start API server",
            "command": "cd d:\\software\\job-automation-service; .\\restart_server.ps1"
        })
    
    if status["jobs"].get("jobs_returned", 0) == 0 and status["api_credentials"]["all_configured"]:
        recommendations.append({
            "priority": "MEDIUM",
            "action": "Restart server to load .env credentials",
            "command": "cd d:\\software\\job-automation-service; .\\restart_server.ps1"
        })
    
    if status["database"]["legacy_jobs"] > 0:
        recommendations.append({
            "priority": "LOW",
            "action": "Backfill legacy jobs with source attribution",
            "command": "cd d:\\software\\job-automation-service; python backfill_legacy_jobs.py"
        })
    
    status["recommendations"] = recommendations
    
    return status

if __name__ == "__main__":
    print("=" * 80)
    print("SYSTEM STATUS SUMMARY")
    print("=" * 80)
    print()
    
    status = get_system_status()
    
    # Print summary
    print("DATABASE:")
    db = status["database"]
    if db.get("connected"):
        print(f"  [OK] Connected - {db.get('total_jobs', 0)} total jobs")
        print(f"       Adzuna jobs: {db.get('adzuna_jobs', 0)}")
        print(f"       Jobs with source: {db.get('jobs_with_source', 0)}")
        print(f"       Jobs with scores: {db.get('jobs_with_scores', 0)}")
        if db.get('legacy_jobs', 0) > 0:
            print(f"       Legacy jobs (no source): {db.get('legacy_jobs', 0)}")
    else:
        print(f"  [FAIL] {db.get('error', 'Unknown error')}")
    
    print()
    print("API CREDENTIALS:")
    creds = status["api_credentials"]
    print(f"  Adzuna API ID: {'[OK]' if creds.get('adzuna_api_id') else '[MISSING]'}")
    print(f"  Adzuna API Key: {'[OK]' if creds.get('adzuna_api_key') else '[MISSING]'}")
    print(f"  JSearch API Key: {'[OK]' if creds.get('jsearch_api_key') else '[MISSING]'}")
    
    print()
    print("API SERVER:")
    server = status["api_server"]
    if server.get("running"):
        print(f"  [OK] Running on port 8004")
        print(f"       Health: {'Healthy' if server.get('healthy') else 'Unhealthy'}")
    else:
        print(f"  [FAIL] Not running - {server.get('error', 'Unknown error')}")
    
    print()
    print("JOB SEARCH:")
    jobs = status["jobs"]
    if jobs.get("search_works"):
        print(f"  [OK] Endpoint working")
        print(f"       Jobs returned: {jobs.get('jobs_returned', 0)}")
        print(f"       Sources: {', '.join(jobs.get('sources_searched', []))}")
    else:
        print(f"  [FAIL] {jobs.get('error', 'Unknown error')}")
    
    print()
    if status["recommendations"]:
        print("RECOMMENDATIONS:")
        for i, rec in enumerate(status["recommendations"], 1):
            print(f"  {i}. [{rec['priority']}] {rec['action']}")
            print(f"     Command: {rec['command']}")
    
    # Save to file
    output_file = "system_status.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, default=str)
    print()
    print(f"Full status saved to: {output_file}")

