"""Testing agents for job automation service."""

import asyncio
import logging
import httpx
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.job_api import (
    IndeedScraper,
    LinkedInScraper,
    GlassdoorScraper,
    ZipRecruiterScraper
)
from app.services.skill_matcher import SkillMatcher
from app.services.cover_letter import CoverLetterGenerator
from app.models.agent_task import AgentTask
from tests.agents.coordinator import AgentType, TaskStatus

logger = logging.getLogger(__name__)


async def scraper_test_agent(task: AgentTask) -> Dict[str, Any]:
    """Test job scrapers from all sources.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with test results
    """
    results = {
        "scrapers_tested": [],
        "success_count": 0,
        "failure_count": 0,
        "jobs_found": 0,
        "errors": [],
        "response_times": {}
    }
    
    scrapers = [
        ("indeed", IndeedScraper()),
        ("linkedin", LinkedInScraper()),
        ("glassdoor", GlassdoorScraper()),
        ("ziprecruiter", ZipRecruiterScraper()),
    ]
    
    for name, scraper in scrapers:
        try:
            logger.info(f"Testing {name} scraper")
            start_time = asyncio.get_event_loop().time()
            
            jobs = await scraper.search_jobs(
                query="Python developer",
                location="Minneapolis, MN",
                limit=5
            )
            
            elapsed = asyncio.get_event_loop().time() - start_time
            
            results["scrapers_tested"].append(name)
            results["success_count"] += 1
            results["jobs_found"] += len(jobs) if jobs else 0
            results["response_times"][name] = elapsed
            
            logger.info(f"{name} scraper: {len(jobs) if jobs else 0} jobs found in {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"{name} scraper failed: {e}")
            results["failure_count"] += 1
            results["errors"].append({name: str(e)})
        finally:
            try:
                await scraper.close()
            except:
                pass
    
    results["total_scrapers"] = len(scrapers)
    results["success_rate"] = results["success_count"] / len(scrapers) if scrapers else 0
    
    return results


async def matcher_test_agent(task: AgentTask) -> Dict[str, Any]:
    """Test skills matching algorithm.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with test results
    """
    db = SessionLocal()
    results = {
        "tests_run": 0,
        "pass_count": 0,
        "fail_count": 0,
        "avg_score": 0.0,
        "test_cases": [],
        "errors": []
    }
    
    try:
        matcher = SkillMatcher(db)
        
        test_cases = [
            {
                "description": "Python FastAPI job - high match",
                "text": "We need a Python developer with FastAPI experience, Docker knowledge, PostgreSQL, and REST API design. Experience with async programming and SQLAlchemy required.",
                "expected_min_score": 0.7
            },
            {
                "description": "Java Spring job - low match",
                "text": "Looking for Java developer with Spring Boot, Maven, Hibernate, and JPA experience. Must know microservices architecture.",
                "expected_min_score": 0.0
            },
            {
                "description": "Full-stack Python job - medium match",
                "text": "Seeking full-stack developer with Python, JavaScript, React, and database experience. Docker and cloud deployment knowledge preferred.",
                "expected_min_score": 0.4
            },
            {
                "description": "DevOps Python job - medium-high match",
                "text": "DevOps engineer needed with Python scripting, Docker, CI/CD, and infrastructure automation experience.",
                "expected_min_score": 0.5
            },
            {
                "description": "Empty description - edge case",
                "text": "",
                "expected_min_score": 0.0
            },
            {
                "description": "Special characters - edge case",
                "text": "Python & FastAPI (v3.0+) developer needed. Experience with SQL/NoSQL databases. C++ knowledge a plus.",
                "expected_min_score": 0.3
            },
            {
                "description": "Very long description",
                "text": "We are seeking an experienced Python developer with extensive knowledge of FastAPI, Docker, PostgreSQL, REST APIs, async programming, SQLAlchemy, pytest, CI/CD pipelines, Linux administration, networking, monitoring tools like Prometheus and Grafana, infrastructure automation, and cloud platforms. The ideal candidate will have 5+ years of experience.",
                "expected_min_score": 0.8
            },
            {
                "description": "Skill variants test",
                "text": "Looking for Python dev, FastAPI framework experience, Postgres database, Docker containers, and RESTful API design.",
                "expected_min_score": 0.6
            }
        ]
        
        scores = []
        for test_case in test_cases:
            try:
                result = matcher.calculate_match_score(test_case["text"])
                score = result.get("overall_match_score", 0.0)
                scores.append(score)
                results["tests_run"] += 1
                
                expected_min = test_case.get("expected_min_score", 0.0)
                passed = score >= expected_min
                
                if passed:
                    results["pass_count"] += 1
                else:
                    results["fail_count"] += 1
                
                results["test_cases"].append({
                    "description": test_case["description"],
                    "score": score,
                    "expected_min": expected_min,
                    "passed": passed,
                    "matched_skills": len(result.get("matched_skills", [])),
                    "skill_details": result.get("matched_skills", [])[:5]  # First 5
                })
                
            except Exception as e:
                logger.error(f"Test case failed: {e}", exc_info=True)
                results["fail_count"] += 1
                results["errors"].append({
                    "test_case": test_case["description"],
                    "error": str(e)
                })
                results["test_cases"].append({
                    "description": test_case["description"],
                    "error": str(e)
                })
        
        results["avg_score"] = sum(scores) / len(scores) if scores else 0.0
        results["pass_rate"] = results["pass_count"] / results["tests_run"] if results["tests_run"] > 0 else 0.0
        
    except Exception as e:
        logger.error(f"Matcher test agent failed: {e}")
        results["error"] = str(e)
    finally:
        db.close()
    
    return results


async def api_test_agent(task: AgentTask) -> Dict[str, Any]:
    """Test API endpoints.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with test results
    """
    base_url = "http://localhost:8004"
    results = {
        "endpoints_tested": [],
        "success_count": 0,
        "failure_count": 0,
        "response_times": {},
        "status_codes": {},
        "errors": []
    }
    
    # Pre-flight check: Verify API server is available
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            health_check = await client.get(f"{base_url}/health")
            if health_check.status_code != 200:
                logger.warning(f"API server health check returned {health_check.status_code}")
    except httpx.ConnectError:
        logger.error("API server is not available - connection failed")
        results["errors"].append({
            "service_check": "API server connection failed - service may not be running"
        })
        return results
    except Exception as e:
        logger.warning(f"API server health check failed: {e}")
    
    endpoints = [
        ("GET", "/health", None),
        ("GET", "/api/v1/jobs/recommended?min_score=0.7&limit=10", None),
        ("GET", "/api/v1/matching/stats", None),
        ("GET", "/api/v1/jobs", None),
        ("POST", "/api/v1/jobs/search", {
            "query": "Python developer",
            "location": "Minneapolis, MN",
            "limit": 5
        }),
        ("POST", "/api/v1/matching/score", {
            "job_description": "Python developer with FastAPI experience"
        }),
        ("POST", "/api/v1/matching/batch-score", {
            "job_descriptions": ["Python developer", "Java developer"]
        }),
        ("POST", "/api/v1/scheduler/start", {
            "location": "Minneapolis, MN",
            "min_match_score": 0.7,
            "limit_per_query": 10
        }),
        ("POST", "/api/v1/scheduler/stop", None),
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for method, path, data in endpoints:
            try:
                logger.info(f"Testing {method} {path}")
                start_time = asyncio.get_event_loop().time()
                
                if method == "GET":
                    response = await client.get(f"{base_url}{path}")
                else:
                    # POST request with data (or empty dict)
                    request_data = data if data is not None else {}
                    response = await client.post(
                        f"{base_url}{path}",
                        json=request_data
                    )
                
                elapsed = asyncio.get_event_loop().time() - start_time
                
                results["endpoints_tested"].append(f"{method} {path}")
                results["response_times"][path] = elapsed
                results["status_codes"][path] = response.status_code
                
                # Validate response
                if 200 <= response.status_code < 300:
                    results["success_count"] += 1
                    # Basic schema validation - check if response is JSON
                    try:
                        response.json()  # Will raise if not JSON
                    except:
                        pass  # Non-JSON responses are OK for some endpoints
                elif response.status_code == 404:
                    results["failure_count"] += 1
                    results["errors"].append({
                        path: f"Endpoint not found (404): {response.text[:200]}",
                        "error_type": "not_found"
                    })
                elif response.status_code == 405:
                    results["failure_count"] += 1
                    results["errors"].append({
                        path: f"Method not allowed (405): Expected {method}",
                        "error_type": "method_not_allowed"
                    })
                elif response.status_code == 422:
                    results["failure_count"] += 1
                    results["errors"].append({
                        path: f"Validation error (422): {response.text[:200]}",
                        "error_type": "validation"
                    })
                else:
                    results["failure_count"] += 1
                    results["errors"].append({
                        path: f"Status {response.status_code}: {response.text[:200]}",
                        "error_type": "http_error"
                    })
                
            except httpx.TimeoutException:
                results["failure_count"] += 1
                results["errors"].append({
                    path: "Request timeout",
                    "error_type": "timeout"
                })
                logger.warning(f"Timeout testing {method} {path}")
            except httpx.ConnectError as e:
                results["failure_count"] += 1
                results["errors"].append({
                    path: f"Connection error - service may not be running: {str(e)}",
                    "error_type": "connection"
                })
                logger.error(f"Connection error testing {method} {path}: {e}")
            except httpx.HTTPStatusError as e:
                results["failure_count"] += 1
                results["errors"].append({
                    path: f"HTTP error {e.response.status_code}: {e.response.text[:200]}",
                    "error_type": "http_error"
                })
                logger.warning(f"HTTP error testing {method} {path}: {e.response.status_code}")
            except Exception as e:
                results["failure_count"] += 1
                results["errors"].append({
                    path: f"Unexpected error: {str(e)}",
                    "error_type": "unexpected"
                })
                logger.error(f"Unexpected error testing {method} {path}: {e}", exc_info=True)
    
    results["total_endpoints"] = len(endpoints)
    results["success_rate"] = results["success_count"] / len(endpoints) if endpoints else 0
    results["avg_response_time"] = (
        sum(results["response_times"].values()) / len(results["response_times"])
        if results["response_times"] else 0
    )
    
    return results


async def cover_letter_test_agent(task: AgentTask) -> Dict[str, Any]:
    """Test cover letter generation.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with test results
    """
    results = {
        "tests_run": 0,
        "success_count": 0,
        "failure_count": 0,
        "avg_length": 0,
        "avg_generation_time": 0.0,
        "errors": []
    }
    
    generator = CoverLetterGenerator()
    
    # Pre-flight check: Verify Ollama is available (optional, will use fallback if not)
    ollama_available = await generator._check_ollama_available()
    if not ollama_available:
        logger.info("Ollama service is not available - will use fallback template generation")
    
    test_jobs = [
        {
            "title": "Python Developer",
            "company": "Test Corp",
            "description": "Python, FastAPI, Docker required. Experience with async programming and PostgreSQL.",
            "url": "https://example.com/job/1"
        },
        {
            "title": "Full-Stack Developer",
            "company": "Tech Inc",
            "description": "Looking for developer with Python, JavaScript, and database experience.",
            "url": "https://example.com/job/2"
        }
    ]
    
    lengths = []
    generation_times = []
    
    for job in test_jobs:
        try:
            logger.info(f"Testing cover letter generation for {job['title']}")
            start_time = asyncio.get_event_loop().time()
            
            # Create mock skill profile result
            skill_profile = {
                "matched_skills": [
                    {"skill": "Python", "proficiency": 5, "category": "technical"},
                    {"skill": "FastAPI", "proficiency": 5, "category": "technical"},
                    {"skill": "Docker", "proficiency": 5, "category": "technical"}
                ],
                "summary": {
                    "overall_match_score": 0.8,
                    "matched_count": 3
                }
            }
            
            letter = await generator.generate_cover_letter(
                job_listing=job,
                skill_profile=skill_profile
            )
            
            elapsed = asyncio.get_event_loop().time() - start_time
            generation_times.append(elapsed)
            
            results["tests_run"] += 1
            
            if letter and len(letter) > 100:  # Basic quality check
                results["success_count"] += 1
                lengths.append(len(letter))
                logger.info(f"Cover letter generated successfully for {job['title']}: {len(letter)} chars")
            else:
                results["failure_count"] += 1
                error_msg = f"Letter too short or empty: {len(letter) if letter else 0} chars"
                logger.warning(f"Cover letter generation failed for {job['title']}: {error_msg}")
                results["errors"].append({
                    job["title"]: error_msg
                })
                
        except Exception as e:
            logger.error(f"Cover letter generation failed for {job['title']}: {e}", exc_info=True)
            results["failure_count"] += 1
            results["errors"].append({
                job["title"]: f"Exception: {str(e)}"
            })
    
    try:
        await generator.close()
    except Exception as e:
        logger.warning(f"Error closing generator: {e}")
    
    results["avg_length"] = sum(lengths) / len(lengths) if lengths else 0
    results["avg_generation_time"] = sum(generation_times) / len(generation_times) if generation_times else 0.0
    results["success_rate"] = results["success_count"] / results["tests_run"] if results["tests_run"] > 0 else 0.0
    
    return results


async def scheduler_test_agent(task: AgentTask) -> Dict[str, Any]:
    """Test scheduled job search functionality.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with test results
    """
    results = {
        "tests_run": 0,
        "success_count": 0,
        "failure_count": 0,
        "jobs_processed": 0,
        "avg_processing_time": 0.0,
        "errors": []
    }
    
    # Test scheduler endpoints
    base_url = "http://localhost:8004"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test scheduler start
        try:
            logger.info("Testing scheduler start")
            response = await client.post(
                f"{base_url}/api/v1/scheduler/start",
                json={
                    "location": "Minneapolis, MN",
                    "min_match_score": 0.7,
                    "limit_per_query": 10
                }
            )
            results["tests_run"] += 1
            
            if response.status_code in [200, 201]:
                results["success_count"] += 1
            else:
                results["failure_count"] += 1
                results["errors"].append({
                    "scheduler_start": f"Status {response.status_code}: {response.text[:200]}"
                })
        except httpx.ConnectError as e:
            results["failure_count"] += 1
            results["errors"].append({
                "scheduler_start": f"Connection error - service may not be running: {str(e)}"
            })
        except Exception as e:
            results["failure_count"] += 1
            results["errors"].append({"scheduler_start": str(e)})
        
        # Test scheduler stop
        try:
            logger.info("Testing scheduler stop")
            response = await client.post(f"{base_url}/api/v1/scheduler/stop")
            results["tests_run"] += 1
            
            if response.status_code in [200, 201]:
                results["success_count"] += 1
            else:
                results["failure_count"] += 1
                results["errors"].append({
                    "scheduler_stop": f"Status {response.status_code}: {response.text[:200]}"
                })
        except httpx.ConnectError as e:
            results["failure_count"] += 1
            results["errors"].append({
                "scheduler_stop": f"Connection error - service may not be running: {str(e)}"
            })
        except Exception as e:
            results["failure_count"] += 1
            results["errors"].append({"scheduler_stop": str(e)})
    
    results["success_rate"] = results["success_count"] / results["tests_run"] if results["tests_run"] > 0 else 0.0
    
    return results


