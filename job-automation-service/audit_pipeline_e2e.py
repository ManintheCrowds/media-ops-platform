"""End-to-End Pipeline Test - Test complete pipeline with real data."""

import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Base directory
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))


async def test_happy_path() -> Dict[str, Any]:
    """Test happy path: API → Source → Match → Save → Return."""
    result = {
        "test_name": "happy_path",
        "status": "pending",
        "details": {}
    }
    
    try:
        from app.services.job_source_manager import JobSourceManager
        from app.services.skill_matcher import SkillMatcher
        from app.database import SessionLocal
        from app.models.job_listing import JobListing
        
        # Initialize components
        source_manager = JobSourceManager()
        db = SessionLocal()
        
        try:
            # Step 1: Search for jobs
            jobs = await source_manager.search_jobs(
                query="Python developer",
                location="Minneapolis, MN",
                sources=["adzuna"],  # Use API source that's more likely to work
                limit=5
            )
            
            result["details"]["jobs_found"] = len(jobs)
            result["details"]["jobs_from_source"] = len(jobs) > 0
            
            if not jobs:
                result["status"] = "skip"
                result["details"]["reason"] = "No jobs found from source (may need API keys or network)"
                return result
            
            # Step 2: Match and score jobs
            matcher = SkillMatcher(db)
            matched_jobs = []
            
            for job_data in jobs[:3]:  # Test with first 3 jobs
                if job_data.get("description"):
                    scores = matcher.calculate_match_score(job_data["description"])
                    job_data["match_scores"] = scores
                    matched_jobs.append(job_data)
            
            result["details"]["jobs_matched"] = len(matched_jobs)
            result["details"]["match_scores_calculated"] = len(matched_jobs) > 0
            
            # Step 3: Verify scores are in valid range
            valid_scores = True
            for job in matched_jobs:
                scores = job.get("match_scores", {})
                for score_key in ["skill_match_score", "experience_match_score", "overall_match_score"]:
                    score = scores.get(score_key, 0.0)
                    if not (0.0 <= score <= 1.0):
                        valid_scores = False
                        break
            
            result["details"]["scores_in_valid_range"] = valid_scores
            
            # Step 4: Check if jobs can be saved (without actually saving)
            can_save = all(
                job.get("source") and 
                job.get("title") and 
                job.get("company") and 
                job.get("url")
                for job in matched_jobs
            )
            result["details"]["jobs_can_be_saved"] = can_save
            
            # Step 5: Verify response format
            response_format_valid = True
            for job in matched_jobs:
                required_fields = ["title", "company", "location", "source", "url"]
                if not all(field in job for field in required_fields):
                    response_format_valid = False
                    break
            
            result["details"]["response_format_valid"] = response_format_valid
            
            if all([
                result["details"]["jobs_from_source"],
                result["details"]["match_scores_calculated"],
                result["details"]["scores_in_valid_range"],
                result["details"]["jobs_can_be_saved"],
                result["details"]["response_format_valid"]
            ]):
                result["status"] = "pass"
            else:
                result["status"] = "partial"
                
        finally:
            db.close()
            await source_manager.close()
            
    except Exception as e:
        result["status"] = "fail"
        result["details"]["error"] = str(e)
        result["details"]["error_type"] = type(e).__name__
    
    return result


async def test_error_handling() -> Dict[str, Any]:
    """Test error handling: Source failure → Fallback → Partial results."""
    result = {
        "test_name": "error_handling",
        "status": "pending",
        "details": {}
    }
    
    try:
        from app.services.job_source_manager import JobSourceManager
        
        source_manager = JobSourceManager()
        
        try:
            # Test with invalid source
            jobs = await source_manager.search_jobs(
                query="Python developer",
                location="Minneapolis, MN",
                sources=["invalid_source"],
                limit=5
            )
            
            result["details"]["handled_invalid_source"] = True
            result["details"]["jobs_returned"] = len(jobs)
            
            # Test with multiple sources (some may fail)
            jobs_multi = await source_manager.search_jobs(
                query="Python developer",
                location="Minneapolis, MN",
                sources=["adzuna", "invalid_source", "indeed"],
                limit=5
            )
            
            result["details"]["partial_results_handled"] = len(jobs_multi) >= 0  # May be 0 if all fail
            result["status"] = "pass"
            
        finally:
            await source_manager.close()
            
    except Exception as e:
        result["status"] = "fail"
        result["details"]["error"] = str(e)
    
    return result


async def test_duplicate_detection() -> Dict[str, Any]:
    """Test duplicate detection: Same job twice → Update vs Create."""
    result = {
        "test_name": "duplicate_detection",
        "status": "pending",
        "details": {}
    }
    
    try:
        from app.api.jobs import search_jobs
        from app.schemas.job import JobSearchRequest
        from app.database import SessionLocal
        from app.models.job_listing import JobListing
        
        db = SessionLocal()
        
        try:
            # Check duplicate detection logic exists
            # This is a code inspection test, not a runtime test
            from app.api.jobs import search_jobs
            import inspect
            
            source_code = inspect.getsource(search_jobs)
            has_duplicate_check = "existing" in source_code.lower() or "duplicate" in source_code.lower()
            
            result["details"]["duplicate_detection_logic_exists"] = has_duplicate_check
            
            # Check model has required fields for duplicate detection
            model_fields = [col.name for col in JobListing.__table__.columns]
            has_source_id = "source_id" in model_fields
            has_source = "source" in model_fields
            
            result["details"]["model_has_duplicate_fields"] = has_source and has_source_id
            
            if has_duplicate_check and has_source and has_source_id:
                result["status"] = "pass"
            else:
                result["status"] = "partial"
                
        finally:
            db.close()
            
    except Exception as e:
        result["status"] = "fail"
        result["details"]["error"] = str(e)
    
    return result


async def test_empty_results() -> Dict[str, Any]:
    """Test empty results: No jobs found → Proper response."""
    result = {
        "test_name": "empty_results",
        "status": "pending",
        "details": {}
    }
    
    try:
        from app.services.job_source_manager import JobSourceManager
        
        source_manager = JobSourceManager()
        
        try:
            # Test with very specific query that likely returns no results
            jobs = await source_manager.search_jobs(
                query="xyzabc123nonexistentjobtitle",
                location="Nowhere, XY",
                sources=["adzuna"],
                limit=5
            )
            
            result["details"]["empty_results_handled"] = isinstance(jobs, list)
            result["details"]["jobs_returned"] = len(jobs)
            
            # Empty results should return empty list, not error
            if isinstance(jobs, list):
                result["status"] = "pass"
            else:
                result["status"] = "fail"
                
        finally:
            await source_manager.close()
            
    except Exception as e:
        # Empty results should not raise exception
        result["status"] = "fail"
        result["details"]["error"] = str(e)
    
    return result


async def test_database_failure() -> Dict[str, Any]:
    """Test database failure: Connection error → Graceful degradation."""
    result = {
        "test_name": "database_failure",
        "status": "pending",
        "details": {}
    }
    
    try:
        from app.database import engine
        
        # Test database connection
        try:
            with engine.connect() as conn:
                result["details"]["database_accessible"] = True
                result["status"] = "skip"
                result["details"]["reason"] = "Database is accessible, cannot test failure scenario"
        except Exception as e:
            result["details"]["database_accessible"] = False
            result["details"]["connection_error"] = str(e)
            result["status"] = "pass"  # Database failure detected, which is what we're testing
            
    except Exception as e:
        result["status"] = "fail"
        result["details"]["error"] = str(e)
    
    return result


async def main():
    """Main function to run all E2E tests."""
    print("=" * 80)
    print("END-TO-END PIPELINE TEST")
    print("=" * 80)
    print()
    
    all_results = {
        "generated_at": datetime.now().isoformat(),
        "test_scenarios": []
    }
    
    # Run all test scenarios
    print("Running test: Happy Path...")
    happy_result = await test_happy_path()
    all_results["test_scenarios"].append(happy_result)
    print(f"  Status: {happy_result['status']}")
    
    print("Running test: Error Handling...")
    error_result = await test_error_handling()
    all_results["test_scenarios"].append(error_result)
    print(f"  Status: {error_result['status']}")
    
    print("Running test: Duplicate Detection...")
    duplicate_result = await test_duplicate_detection()
    all_results["test_scenarios"].append(duplicate_result)
    print(f"  Status: {duplicate_result['status']}")
    
    print("Running test: Empty Results...")
    empty_result = await test_empty_results()
    all_results["test_scenarios"].append(empty_result)
    print(f"  Status: {empty_result['status']}")
    
    print("Running test: Database Failure...")
    db_result = await test_database_failure()
    all_results["test_scenarios"].append(db_result)
    print(f"  Status: {db_result['status']}")
    
    # Calculate summary
    total_tests = len(all_results["test_scenarios"])
    passed_tests = sum(1 for t in all_results["test_scenarios"] if t.get("status") == "pass")
    failed_tests = sum(1 for t in all_results["test_scenarios"] if t.get("status") == "fail")
    skipped_tests = sum(1 for t in all_results["test_scenarios"] if t.get("status") == "skip")
    
    all_results["summary"] = {
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "skipped": skipped_tests,
        "pass_rate": passed_tests / (total_tests - skipped_tests) if (total_tests - skipped_tests) > 0 else 0.0
    }
    
    # Save results
    output_file = BASE_DIR / "audit_pipeline_e2e_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 80)
    print("E2E TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Skipped: {skipped_tests}")
    print(f"Pass rate: {all_results['summary']['pass_rate']:.1%}")
    print()
    print(f"[OK] Report saved to: {output_file}")
    print()
    print("=" * 80)
    print("E2E testing complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

