"""Integration test agent for end-to-end workflows."""

import asyncio
import logging
import httpx
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.agent_task import AgentTask
from app.models.job_listing import JobListing
from app.models.application import Application

logger = logging.getLogger(__name__)


async def integration_test_agent(task: AgentTask) -> Dict[str, Any]:
    """Test end-to-end workflows.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with test results
    """
    results = {
        "workflows_tested": [],
        "success_count": 0,
        "failure_count": 0,
        "test_scenarios": [],
        "errors": []
    }
    
    base_url = "http://localhost:8004"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Workflow 1: Search -> Match -> Get Recommended
        try:
            logger.info("Testing workflow: Search -> Match -> Recommended")
            
            # Step 1: Search for jobs
            search_response = await client.post(
                f"{base_url}/api/v1/jobs/search",
                json={
                    "query": "Python developer",
                    "location": "Minneapolis, MN",
                    "limit": 5
                }
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                jobs_found = len(search_data.get("jobs", []))
                
                # Step 2: Get recommended jobs
                if jobs_found > 0:
                    rec_response = await client.get(
                        f"{base_url}/api/v1/jobs/recommended?min_score=0.5&limit=10"
                    )
                    
                    if rec_response.status_code == 200:
                        results["workflows_tested"].append("search_to_recommended")
                        results["success_count"] += 1
                        results["test_scenarios"].append({
                            "workflow": "search_to_recommended",
                            "status": "passed",
                            "jobs_searched": jobs_found,
                            "recommended_count": len(rec_response.json())
                        })
                    else:
                        results["failure_count"] += 1
                        results["errors"].append({
                            "workflow": "search_to_recommended",
                            "step": "get_recommended",
                            "error": f"Status {rec_response.status_code}"
                        })
                else:
                    results["test_scenarios"].append({
                        "workflow": "search_to_recommended",
                        "status": "skipped",
                        "reason": "No jobs found in search"
                    })
            else:
                results["failure_count"] += 1
                results["errors"].append({
                    "workflow": "search_to_recommended",
                    "step": "search",
                    "error": f"Status {search_response.status_code}"
                })
                
        except Exception as e:
            logger.error(f"Workflow test failed: {e}", exc_info=True)
            results["failure_count"] += 1
            results["errors"].append({"workflow": "search_to_recommended", "error": str(e)})
        
        # Workflow 2: Match Score -> Batch Score
        try:
            logger.info("Testing workflow: Match Score -> Batch Score")
            
            # Step 1: Single score
            score_response = await client.post(
                f"{base_url}/api/v1/matching/score",
                json={"job_description": "Python developer with FastAPI and Docker experience"}
            )
            
            if score_response.status_code == 200:
                score_data = score_response.json()
                
                # Step 2: Batch score
                batch_response = await client.post(
                    f"{base_url}/api/v1/matching/batch-score",
                    json={
                        "job_descriptions": [
                            "Python developer",
                            "Java developer",
                            "DevOps engineer"
                        ]
                    }
                )
                
                if batch_response.status_code == 200:
                    results["workflows_tested"].append("score_to_batch")
                    results["success_count"] += 1
                    results["test_scenarios"].append({
                        "workflow": "score_to_batch",
                        "status": "passed",
                        "single_score": score_data.get("overall_match_score", 0),
                        "batch_count": len(batch_response.json().get("scores", []))
                    })
                else:
                    results["failure_count"] += 1
                    results["errors"].append({
                        "workflow": "score_to_batch",
                        "step": "batch_score",
                        "error": f"Status {batch_response.status_code}"
                    })
            else:
                results["failure_count"] += 1
                results["errors"].append({
                    "workflow": "score_to_batch",
                    "step": "single_score",
                    "error": f"Status {score_response.status_code}"
                })
                
        except Exception as e:
            logger.error(f"Workflow test failed: {e}", exc_info=True)
            results["failure_count"] += 1
            results["errors"].append({"workflow": "score_to_batch", "error": str(e)})
        
        # Workflow 3: Database State Validation
        try:
            logger.info("Testing database state validation")
            db = SessionLocal()
            
            try:
                # Check job listings exist
                job_count = db.query(JobListing).count()
                
                # Check applications table accessible
                app_count = db.query(Application).count()
                
                results["workflows_tested"].append("database_validation")
                results["success_count"] += 1
                results["test_scenarios"].append({
                    "workflow": "database_validation",
                    "status": "passed",
                    "job_listings": job_count,
                    "applications": app_count
                })
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Database validation failed: {e}", exc_info=True)
            results["failure_count"] += 1
            results["errors"].append({"workflow": "database_validation", "error": str(e)})
    
    results["total_workflows"] = len(results["workflows_tested"])
    results["success_rate"] = results["success_count"] / max(results["total_workflows"], 1)
    
    return results

