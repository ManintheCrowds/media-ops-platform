#!/usr/bin/env python3
"""Comprehensive test script for all service endpoints."""
import httpx
import json
import time
from typing import Dict, List, Tuple, Optional
from pathlib import Path

BASE_URL = "http://localhost:8004"
DEBUG_LOG_PATH = Path("C:/Users/artin/software/.cursor/debug.log")

# #region agent log
def write_debug_log(session_id: str, run_id: str, hypothesis_id: str, location: str, message: str, data: Dict):
    """Write debug log entry in NDJSON format."""
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
        pass  # Silently fail if logging fails
# #endregion agent log

# Test results storage
results: List[Tuple[str, bool, str, Optional[int]]] = []

def check_service_available() -> bool:
    """Check if the service is accessible before running tests."""
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=5.0)
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False

def validate_response_schema(path: str, response_data: Dict) -> Tuple[bool, str]:
    """Validate response data matches expected schema for specific endpoints."""
    try:
        # Validate /api/v1/jobs/search response
        if path == "/api/v1/jobs/search":
            if not isinstance(response_data, dict):
                return False, "Response is not a dictionary"
            required_fields = ["jobs", "count", "sources_searched"]
            for field in required_fields:
                if field not in response_data:
                    return False, f"Missing required field: {field}"
            if not isinstance(response_data["jobs"], list):
                return False, "Field 'jobs' must be a list"
            if not isinstance(response_data["count"], int):
                return False, "Field 'count' must be an integer"
            if not isinstance(response_data["sources_searched"], list):
                return False, "Field 'sources_searched' must be a list"
            # Validate job items if present
            for job in response_data["jobs"]:
                if not isinstance(job, dict):
                    return False, "Job items must be dictionaries"
                job_required = ["id", "title", "company", "source", "url", "skill_match_score", 
                               "experience_match_score", "overall_match_score", "scraped_at", "is_active"]
                for field in job_required:
                    if field not in job:
                        return False, f"Job missing required field: {field}"
        
        # Validate /api/v1/jobs/recommended response
        elif path.startswith("/api/v1/jobs/recommended"):
            if not isinstance(response_data, list):
                return False, "Response must be a list"
            for job in response_data:
                if not isinstance(job, dict):
                    return False, "Job items must be dictionaries"
                job_required = ["id", "title", "company", "source", "url", "skill_match_score",
                               "experience_match_score", "overall_match_score", "scraped_at", "is_active"]
                for field in job_required:
                    if field not in job:
                        return False, f"Job missing required field: {field}"
        
        # Validate /api/v1/matching/score response
        elif path == "/api/v1/matching/score":
            if not isinstance(response_data, dict):
                return False, "Response is not a dictionary"
            required_fields = ["skill_match_score", "experience_match_score", "overall_match_score", "matched_skills"]
            for field in required_fields:
                if field not in response_data:
                    return False, f"Missing required field: {field}"
            if not isinstance(response_data["matched_skills"], list):
                return False, "Field 'matched_skills' must be a list"
        
        # Validate /api/v1/matching/batch-score response
        elif path == "/api/v1/matching/batch-score":
            if not isinstance(response_data, dict):
                return False, "Response is not a dictionary"
            if "scores" not in response_data:
                return False, "Missing required field: scores"
            if not isinstance(response_data["scores"], list):
                return False, "Field 'scores' must be a list"
            for score in response_data["scores"]:
                if not isinstance(score, dict):
                    return False, "Score items must be dictionaries"
                score_required = ["skill_match_score", "experience_match_score", "overall_match_score", "matched_skills"]
                for field in score_required:
                    if field not in score:
                        return False, f"Score missing required field: {field}"
        
        return True, "Schema validation passed"
    except Exception as e:
        return False, f"Schema validation error: {str(e)}"


def test_endpoint(
    method: str, 
    path: str, 
    json_body: Optional[Dict] = None,
    params: Optional[Dict] = None,
    expected_status: int = 200,
    session_id: str = "debug-session",
    run_id: str = "run1"
) -> Tuple[bool, str, int]:
    """Test a single endpoint and return (success, message, status_code)."""
    url = f"{BASE_URL}{path}"
    start_time = time.time()
    
    # #region agent log
    write_debug_log(
        session_id, run_id, "H1",
        f"test_all_endpoints.py:test_endpoint",
        f"Testing endpoint: {method} {path}",
        {
            "method": method,
            "path": path,
            "url": url,
            "json_body": json_body,
            "params": params,
            "expected_status": expected_status
        }
    )
    # #endregion agent log
    
    try:
        # #region agent log
        write_debug_log(
            session_id, run_id, "H2",
            f"test_all_endpoints.py:test_endpoint",
            f"Before HTTP request: {method} {path}",
            {"url": url, "has_json_body": json_body is not None, "has_params": params is not None}
        )
        # #endregion agent log
        
        if method == "GET":
            response = httpx.get(url, params=params, timeout=30.0)
        elif method == "POST":
            response = httpx.post(url, json=json_body, params=params, timeout=30.0)
        elif method == "PATCH":
            response = httpx.patch(url, json=json_body, timeout=30.0)
        else:
            response = httpx.request(method, url, json=json_body, timeout=30.0)
        
        elapsed_time = time.time() - start_time
        success = response.status_code == expected_status
        response_text = response.text[:200] if response.text else ""
        
        # Validate response schema for successful responses
        schema_valid = True
        schema_msg = ""
        if success and response.status_code == 200:
            try:
                response_json = response.json()
                schema_valid, schema_msg = validate_response_schema(path, response_json)
                if not schema_valid:
                    success = False
                    response_text = f"Schema validation failed: {schema_msg}"
            except Exception as e:
                # If response is not JSON, that's OK for some endpoints
                pass
        
        # #region agent log
        write_debug_log(
            session_id, run_id, "H3",
            f"test_all_endpoints.py:test_endpoint",
            f"After HTTP request: {method} {path}",
            {
                "status_code": response.status_code,
                "expected_status": expected_status,
                "success": success,
                "schema_valid": schema_valid,
                "elapsed_time_ms": round(elapsed_time * 1000, 2),
                "response_headers": dict(response.headers),
                "response_text_preview": response_text,
                "response_size": len(response.text) if response.text else 0
            }
        )
        # #endregion agent log
        
        return success, response_text, response.status_code
    except httpx.ConnectError as e:
        elapsed_time = time.time() - start_time
        # #region agent log
        write_debug_log(
            session_id, run_id, "H4",
            f"test_all_endpoints.py:test_endpoint",
            f"Connection error: {method} {path}",
            {
                "error_type": "ConnectError",
                "error_message": str(e),
                "elapsed_time_ms": round(elapsed_time * 1000, 2),
                "url": url
            }
        )
        # #endregion agent log
        return False, f"Connection refused - Service may not be running", 0
    except httpx.TimeoutException as e:
        elapsed_time = time.time() - start_time
        # #region agent log
        write_debug_log(
            session_id, run_id, "H5",
            f"test_all_endpoints.py:test_endpoint",
            f"Timeout error: {method} {path}",
            {
                "error_type": "TimeoutException",
                "error_message": str(e),
                "elapsed_time_ms": round(elapsed_time * 1000, 2),
                "url": url
            }
        )
        # #endregion agent log
        return False, f"Request timeout", 0
    except httpx.HTTPStatusError as e:
        elapsed_time = time.time() - start_time
        # #region agent log
        write_debug_log(
            session_id, run_id, "H6",
            f"test_all_endpoints.py:test_endpoint",
            f"HTTP status error: {method} {path}",
            {
                "error_type": "HTTPStatusError",
                "status_code": e.response.status_code if e.response else None,
                "error_message": str(e),
                "elapsed_time_ms": round(elapsed_time * 1000, 2),
                "url": url
            }
        )
        # #endregion agent log
        return False, f"HTTP {e.response.status_code if e.response else 'unknown'}", e.response.status_code if e.response else 0
    except Exception as e:
        elapsed_time = time.time() - start_time
        # #region agent log
        write_debug_log(
            session_id, run_id, "H7",
            f"test_all_endpoints.py:test_endpoint",
            f"Unexpected error: {method} {path}",
            {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "elapsed_time_ms": round(elapsed_time * 1000, 2),
                "url": url
            }
        )
        # #endregion agent log
        return False, str(e), 0

def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_result(name: str, success: bool, message: str, status_code: int):
    """Print a test result."""
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} {name}")
    if not success or status_code != 200:
        print(f"    Status: {status_code}")
        if message:
            print(f"    Response: {message[:150]}")

if __name__ == "__main__":
    import sys
    session_id = "debug-session"
    run_id = f"run-{int(time.time())}"
    
    # Clear previous log file
    try:
        if DEBUG_LOG_PATH.exists():
            DEBUG_LOG_PATH.unlink()
    except Exception:
        pass
    
    # #region agent log
    write_debug_log(
        session_id, run_id, "H0",
        "test_all_endpoints.py:__main__",
        "Starting comprehensive endpoint test suite",
        {"base_url": BASE_URL, "total_endpoints": 17}
    )
    # #endregion agent log
    
    print("="*60)
    print("  COMPREHENSIVE SERVICE ENDPOINT TEST")
    print("="*60)
    
    # Check if service is available first
    print("\nChecking if service is accessible...")
    # #region agent log
    write_debug_log(
        session_id, run_id, "H0",
        "test_all_endpoints.py:__main__",
        "Checking service availability",
        {"base_url": BASE_URL, "health_endpoint": f"{BASE_URL}/health"}
    )
    # #endregion agent log
    
    if not check_service_available():
        # #region agent log
        write_debug_log(
            session_id, run_id, "H0",
            "test_all_endpoints.py:__main__",
            "Service not available - exiting early",
            {"base_url": BASE_URL, "reason": "health_check_failed"}
        )
        # #endregion agent log
        print("[ERROR] Service is not accessible!")
        print(f"  Cannot connect to {BASE_URL}")
        print("\nPlease ensure:")
        print("  1. Docker Desktop is running")
        print("  2. Service container is started (run: .\\start_service.ps1)")
        print("  3. Service is healthy (run: python check_service.py)")
        sys.exit(1)
    
    # #region agent log
    write_debug_log(
        session_id, run_id, "H0",
        "test_all_endpoints.py:__main__",
        "Service is accessible - starting endpoint tests",
        {"base_url": BASE_URL}
    )
    # #endregion agent log
    
    print("[OK] Service is accessible, starting tests...\n")
    
    # Health endpoint
    print_section("Health Check")
    success, msg, status = test_endpoint("GET", "/health", session_id=session_id, run_id=run_id)
    results.append(("GET /health", success, msg, status))
    print_result("GET /health", success, msg, status)
    
    # Jobs endpoints
    print_section("Jobs Endpoints")
    
    # POST /api/v1/jobs/search
    success, msg, status = test_endpoint(
        "POST", 
        "/api/v1/jobs/search",
        {"query": "Python developer", "location": "Minneapolis, MN", "limit": 5},
        session_id=session_id, run_id=run_id
    )
    results.append(("POST /api/v1/jobs/search", success, msg, status))
    print_result("POST /api/v1/jobs/search", success, msg, status)
    
    # GET /api/v1/jobs
    success, msg, status = test_endpoint("GET", "/api/v1/jobs", params={"limit": 10}, session_id=session_id, run_id=run_id)
    results.append(("GET /api/v1/jobs", success, msg, status))
    print_result("GET /api/v1/jobs", success, msg, status)
    
    # GET /api/v1/jobs/recommended
    success, msg, status = test_endpoint(
        "GET", 
        "/api/v1/jobs/recommended",
        params={"min_score": 0.7, "limit": 10},
        session_id=session_id, run_id=run_id
    )
    results.append(("GET /api/v1/jobs/recommended", success, msg, status))
    print_result("GET /api/v1/jobs/recommended", success, msg, status)
    
    # GET /api/v1/jobs/{id} (test with id=1, may fail if no jobs)
    success, msg, status = test_endpoint("GET", "/api/v1/jobs/1", expected_status=200, session_id=session_id, run_id=run_id)
    results.append(("GET /api/v1/jobs/1", success, msg, status))
    print_result("GET /api/v1/jobs/1", success, msg, status)
    
    # POST /api/v1/jobs/{id}/refresh
    success, msg, status = test_endpoint("POST", "/api/v1/jobs/1/refresh", expected_status=200, session_id=session_id, run_id=run_id)
    results.append(("POST /api/v1/jobs/1/refresh", success, msg, status))
    print_result("POST /api/v1/jobs/1/refresh", success, msg, status)
    
    # Matching endpoints
    print_section("Matching Endpoints")
    
    # POST /api/v1/matching/score
    success, msg, status = test_endpoint(
        "POST",
        "/api/v1/matching/score",
        {"job_description": "Python developer with FastAPI experience"},
        session_id=session_id, run_id=run_id
    )
    results.append(("POST /api/v1/matching/score", success, msg, status))
    print_result("POST /api/v1/matching/score", success, msg, status)
    
    # POST /api/v1/matching/batch-score
    success, msg, status = test_endpoint(
        "POST",
        "/api/v1/matching/batch-score",
        {"job_descriptions": ["Python developer", "Java developer"]},
        session_id=session_id, run_id=run_id
    )
    results.append(("POST /api/v1/matching/batch-score", success, msg, status))
    print_result("POST /api/v1/matching/batch-score", success, msg, status)
    
    # GET /api/v1/matching/stats
    success, msg, status = test_endpoint("GET", "/api/v1/matching/stats", session_id=session_id, run_id=run_id)
    results.append(("GET /api/v1/matching/stats", success, msg, status))
    print_result("GET /api/v1/matching/stats", success, msg, status)
    
    # Scheduler endpoints
    print_section("Scheduler Endpoints")
    
    # POST /api/v1/scheduler/start
    success, msg, status = test_endpoint(
        "POST",
        "/api/v1/scheduler/start",
        {"location": "Minneapolis, MN", "min_match_score": 0.7},
        session_id=session_id, run_id=run_id
    )
    results.append(("POST /api/v1/scheduler/start", success, msg, status))
    print_result("POST /api/v1/scheduler/start", success, msg, status)
    
    # POST /api/v1/scheduler/stop
    success, msg, status = test_endpoint("POST", "/api/v1/scheduler/stop", session_id=session_id, run_id=run_id)
    results.append(("POST /api/v1/scheduler/stop", success, msg, status))
    print_result("POST /api/v1/scheduler/stop", success, msg, status)
    
    # POST /api/v1/scheduler/search
    success, msg, status = test_endpoint(
        "POST",
        "/api/v1/scheduler/search",
        {"location": "Minneapolis, MN", "min_match_score": 0.7},
        session_id=session_id, run_id=run_id
    )
    results.append(("POST /api/v1/scheduler/search", success, msg, status))
    print_result("POST /api/v1/scheduler/search", success, msg, status)
    
    # POST /api/v1/scheduler/daily
    success, msg, status = test_endpoint("POST", "/api/v1/scheduler/daily", session_id=session_id, run_id=run_id)
    results.append(("POST /api/v1/scheduler/daily", success, msg, status))
    print_result("POST /api/v1/scheduler/daily", success, msg, status)
    
    # POST /api/v1/scheduler/weekly
    success, msg, status = test_endpoint("POST", "/api/v1/scheduler/weekly", session_id=session_id, run_id=run_id)
    results.append(("POST /api/v1/scheduler/weekly", success, msg, status))
    print_result("POST /api/v1/scheduler/weekly", success, msg, status)
    
    # Applications endpoints
    print_section("Applications Endpoints")
    
    # GET /api/v1/applications
    success, msg, status = test_endpoint("GET", "/api/v1/applications", params={"limit": 10}, session_id=session_id, run_id=run_id)
    results.append(("GET /api/v1/applications", success, msg, status))
    print_result("GET /api/v1/applications", success, msg, status)
    
    # GET /api/v1/applications/pending-followups
    success, msg, status = test_endpoint("GET", "/api/v1/applications/pending-followups", session_id=session_id, run_id=run_id)
    results.append(("GET /api/v1/applications/pending-followups", success, msg, status))
    print_result("GET /api/v1/applications/pending-followups", success, msg, status)
    
    # GET /api/v1/applications/{id} (test with id=1, may fail if no applications)
    success, msg, status = test_endpoint("GET", "/api/v1/applications/1", expected_status=200, session_id=session_id, run_id=run_id)
    results.append(("GET /api/v1/applications/1", success, msg, status))
    print_result("GET /api/v1/applications/1", success, msg, status)
    
    # Summary
    print_section("Test Summary")
    total = len(results)
    passed = sum(1 for _, success, _, _ in results if success)
    failed = total - passed
    
    # #region agent log
    write_debug_log(
        session_id, run_id, "H0",
        "test_all_endpoints.py:__main__",
        "Test suite completed",
        {
            "total_endpoints": total,
            "passed": passed,
            "failed": failed,
            "success_rate": round((passed/total*100), 1) if total > 0 else 0,
            "failed_endpoints": [name for name, success, _, _ in results if not success]
        }
    )
    # #endregion agent log
    
    print(f"Total endpoints tested: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(passed/total*100):.1f}%")
    
    if failed > 0:
        print("\nFailed endpoints:")
        for name, success, msg, status in results:
            if not success:
                print(f"  - {name} (Status: {status})")
    
    print(f"\nDebug logs written to: {DEBUG_LOG_PATH}")
    print("\n" + "="*60)

