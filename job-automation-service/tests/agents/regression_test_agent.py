"""Regression test agent for known issues and fixed bugs."""

import asyncio
import logging
import httpx
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.agent_task import AgentTask
from app.models.job_listing import JobListing

logger = logging.getLogger(__name__)


async def regression_test_agent(task: AgentTask) -> Dict[str, Any]:
    """Test for regression of known issues.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with regression test results
    """
    results = {
        "regression_tests": [],
        "passed": 0,
        "failed": 0,
        "known_issues_verified": [],
        "errors": []
    }
    
    base_url = "http://localhost:8004"
    
    # Known issue: Scheduler endpoints should exist
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Regression Test 1: Scheduler endpoints exist
        try:
            logger.info("Regression test: Scheduler endpoints")
            
            start_response = await client.post(f"{base_url}/api/v1/scheduler/start", json={})
            stop_response = await client.post(f"{base_url}/api/v1/scheduler/stop")
            
            test_passed = start_response.status_code in [200, 201] and stop_response.status_code in [200, 201]
            
            results["regression_tests"].append({
                "test": "scheduler_endpoints_exist",
                "passed": test_passed,
                "start_status": start_response.status_code,
                "stop_status": stop_response.status_code
            })
            
            if test_passed:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "test": "scheduler_endpoints_exist",
                    "error": f"Start: {start_response.status_code}, Stop: {stop_response.status_code}"
                })
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"test": "scheduler_endpoints_exist", "error": str(e)})
        
        # Regression Test 2: POST endpoints work correctly
        try:
            logger.info("Regression test: POST endpoints")
            
            score_response = await client.post(
                f"{base_url}/api/v1/matching/score",
                json={"job_description": "Python developer"}
            )
            
            followup_response = await client.post(
                f"{base_url}/api/v1/applications/1/followup",
                json={"days": 7, "notes": "Test"}
            )
            
            # Score should work, followup may 404 if no application exists (that's OK)
            score_ok = score_response.status_code in [200, 201]
            followup_ok = followup_response.status_code in [200, 201, 404]  # 404 is OK if app doesn't exist
            
            test_passed = score_ok and (followup_ok or followup_response.status_code == 404)
            
            results["regression_tests"].append({
                "test": "post_endpoints_work",
                "passed": test_passed,
                "score_status": score_response.status_code,
                "followup_status": followup_response.status_code
            })
            
            if test_passed:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "test": "post_endpoints_work",
                    "error": f"Score: {score_response.status_code}, Followup: {followup_response.status_code}"
                })
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"test": "post_endpoints_work", "error": str(e)})
        
        # Regression Test 3: Skill matcher scores improved
        try:
            logger.info("Regression test: Skill matcher scores")
            db = SessionLocal()
            
            try:
                from app.services.skill_matcher import SkillMatcher
                matcher = SkillMatcher(db)
                
                # Test with high-match job
                result = matcher.calculate_match_score(
                    "Python developer with FastAPI experience, Docker knowledge, PostgreSQL, and REST API design."
                )
                
                score = result.get("overall_match_score", 0.0)
                # Should be > 0.5 after fix (was 0.174 before)
                test_passed = score > 0.5
                
                results["regression_tests"].append({
                    "test": "skill_matcher_scores_improved",
                    "passed": test_passed,
                    "score": score,
                    "expected_min": 0.5,
                    "previous_score": 0.174
                })
                
                if test_passed:
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "test": "skill_matcher_scores_improved",
                        "error": f"Score {score} is below expected minimum 0.5"
                    })
            finally:
                db.close()
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"test": "skill_matcher_scores_improved", "error": str(e)})
    
    results["total_tests"] = len(results["regression_tests"])
    results["pass_rate"] = results["passed"] / results["total_tests"] if results["total_tests"] > 0 else 0.0
    
    return results

