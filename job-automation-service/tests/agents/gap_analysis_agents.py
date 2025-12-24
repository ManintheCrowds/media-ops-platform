"""Gap analysis agents for identifying missing features and issues."""

import asyncio
import logging
import ast
import httpx
from typing import Dict, Any, List
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from app.database import SessionLocal
from app.models.agent_task import AgentTask

logger = logging.getLogger(__name__)


async def gap_analysis_agent(task: AgentTask) -> Dict[str, Any]:
    """Analyze gaps between requirements and implementation.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with gap analysis results
    """
    gaps = {
        "missing_features": [],
        "incomplete_features": [],
        "documentation_gaps": [],
        "test_gaps": [],
        "api_coverage": {},
        "database_schema": {},
        "errors": []
    }
    
    # Check API endpoint coverage
    # Define endpoints with their expected HTTP methods
    endpoint_configs = [
        ("/api/v1/jobs/search", "POST"),
        ("/api/v1/jobs", "GET"),
        ("/api/v1/jobs/{id}", "GET"),
        ("/api/v1/jobs/recommended", "GET"),
        ("/api/v1/jobs/refresh", "POST"),
        ("/api/v1/applications", "GET"),
        ("/api/v1/applications/{id}", "GET"),
        ("/api/v1/applications/{id}/followup", "POST"),
        ("/api/v1/matching/score", "POST"),
        ("/api/v1/matching/stats", "GET"),
        ("/api/v1/matching/batch-score", "POST"),
        ("/api/v1/scheduler/start", "POST"),
        ("/api/v1/scheduler/stop", "POST"),
    ]
    
    base_url = "http://localhost:8004"
    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint, method in endpoint_configs:
            # Replace path parameters for testing
            test_endpoint = endpoint.replace("{id}", "1")
            try:
                # Prepare request data for POST endpoints
                request_data = {}
                if method == "POST":
                    if "search" in endpoint:
                        request_data = {"query": "Python developer", "location": "Minneapolis, MN", "limit": 5}
                    elif "score" in endpoint:
                        request_data = {"job_description": "Python developer with FastAPI experience"}
                    elif "batch-score" in endpoint:
                        request_data = {"job_descriptions": ["Python developer", "Java developer"]}
                    elif "followup" in endpoint:
                        request_data = {"days": 7, "notes": "Test followup"}
                    elif "start" in endpoint or "stop" in endpoint:
                        request_data = {}  # Optional body
                    elif "refresh" in endpoint:
                        request_data = {"job_id": 1}
                
                # Test endpoint with correct method
                if method == "POST":
                    response = await client.post(f"{base_url}{test_endpoint}", json=request_data)
                else:
                    response = await client.get(f"{base_url}{test_endpoint}")
                
                gaps["api_coverage"][endpoint] = {
                    "exists": response.status_code in [200, 201, 401, 403, 404, 422],  # 404/422 may indicate route exists
                    "status_code": response.status_code,
                    "method": method
                }
            except httpx.ConnectError:
                gaps["api_coverage"][endpoint] = {
                    "exists": False,
                    "error": "Service not running",
                    "method": method
                }
                gaps["errors"].append(f"Connection error for {endpoint}")
            except Exception as e:
                logger.error(f"Error testing endpoint {endpoint}: {e}", exc_info=True)
                gaps["api_coverage"][endpoint] = {
                    "exists": False,
                    "error": str(e),
                    "method": method
                }
                gaps["errors"].append(f"Error testing {endpoint}: {str(e)}")
    
    # Check database schema completeness
    db = SessionLocal()
    try:
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()
        
        expected_tables = ["job_listings", "applications", "skill_profiles", "agent_tasks", "agent_locks"]
        for table in expected_tables:
            if table not in tables:
                gaps["missing_features"].append({
                    "feature": f"Database table: {table}",
                    "priority": "high",
                    "reason": "Required table missing",
                    "category": "database"
                })
            else:
                gaps["database_schema"][table] = {
                    "exists": True,
                    "columns": len(inspector.get_columns(table))
                }
    except Exception as e:
        logger.error(f"Error checking database schema: {e}")
        gaps["database_schema"]["error"] = str(e)
    finally:
        db.close()
    
    # Check for missing features based on plan
    plan_file = Path(".cursor/plans/job_application_automation_system_b3bffe60.plan.md")
    if not plan_file.exists():
        # Try alternative locations
        plan_file = Path("../.cursor/plans/job_application_automation_system_b3bffe60.plan.md")
    
    if plan_file.exists():
        try:
            plan_content = plan_file.read_text()
            
            # Check for auto-submit (mentioned as future enhancement)
            if "auto-submit" in plan_content.lower() and "future" in plan_content.lower():
                gaps["missing_features"].append({
                    "feature": "Auto-submit applications",
                    "priority": "medium",
                    "reason": "Listed as future enhancement",
                    "category": "feature"
                })
        except Exception as e:
            logger.warning(f"Could not read plan file: {e}")
    
    # Check code structure
    code_files = [
        "app/api/jobs.py",
        "app/api/applications.py",
        "app/api/matching.py",
        "app/api/scheduler.py",
        "app/services/job_scraper.py",
        "app/services/skill_matcher.py",
        "app/services/cover_letter.py",
    ]
    
    for file_path in code_files:
        path = Path(file_path)
        if not path.exists():
            gaps["missing_features"].append({
                "feature": f"Code file: {file_path}",
                "priority": "high",
                "reason": "Required file missing",
                "category": "code"
            })
    
    return gaps


async def performance_analysis_agent(task: AgentTask) -> Dict[str, Any]:
    """Analyze performance characteristics.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with performance analysis results
    """
    results = {
        "endpoint_performance": {},
        "database_performance": {},
        "scraper_performance": {},
        "recommendations": []
    }
    
    base_url = "http://localhost:8004"
    endpoints = [
        "/health",
        "/api/v1/jobs/recommended?min_score=0.7&limit=10",
        "/api/v1/matching/stats",
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint in endpoints:
            times = []
            success_count = 0
            
            for i in range(5):  # 5 requests
                try:
                    start = asyncio.get_event_loop().time()
                    response = await client.get(f"{base_url}{endpoint}")
                    elapsed = asyncio.get_event_loop().time() - start
                    
                    if response.status_code == 200:
                        times.append(elapsed)
                        success_count += 1
                except Exception as e:
                    logger.warning(f"Request {i+1} to {endpoint} failed: {e}")
            
            if times:
                avg_time = sum(times) / len(times)
                results["endpoint_performance"][endpoint] = {
                    "avg_ms": avg_time * 1000,
                    "min_ms": min(times) * 1000,
                    "max_ms": max(times) * 1000,
                    "success_rate": success_count / 5,
                    "requests": len(times)
                }
                
                if avg_time > 1.0:  # > 1 second
                    results["recommendations"].append({
                        "type": "performance",
                        "endpoint": endpoint,
                        "issue": f"Slow response time: {avg_time:.2f}s",
                        "suggestion": "Consider caching or optimization",
                        "priority": "medium"
                    })
                elif avg_time > 0.5:  # > 500ms
                    results["recommendations"].append({
                        "type": "performance",
                        "endpoint": endpoint,
                        "issue": f"Moderate response time: {avg_time:.2f}s",
                        "suggestion": "Monitor and optimize if needed",
                        "priority": "low"
                    })
            else:
                results["endpoint_performance"][endpoint] = {
                    "error": "All requests failed"
                }
    
    return results


async def security_analysis_agent(task: AgentTask) -> Dict[str, Any]:
    """Analyze security aspects.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with security findings
    """
    findings = {
        "vulnerabilities": [],
        "best_practices": [],
        "recommendations": []
    }
    
    # Check for common security issues
    code_files = [
        "app/api/jobs.py",
        "app/api/applications.py",
        "app/services/job_scraper.py",
        "app/database.py",
    ]
    
    for file_path in code_files:
        path = Path(file_path)
        if not path.exists():
            continue
        
        try:
            content = path.read_text()
            
            # Check for SQL injection risks
            if "f\"" in content and "SELECT" in content.upper():
                # More sophisticated check needed, but basic pattern
                findings["vulnerabilities"].append({
                    "file": file_path,
                    "issue": "Potential SQL injection risk with f-strings",
                    "severity": "medium",
                    "line": "Check for f-string SQL queries"
                })
            
            # Check for exposed secrets
            if "password" in content.lower() and "=" in content:
                # Check if it's hardcoded (basic check)
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'password' in line.lower() and '=' in line and '"' in line:
                        if 'env' not in line.lower() and 'config' not in line.lower():
                            findings["vulnerabilities"].append({
                                "file": file_path,
                                "issue": "Potential hardcoded credentials",
                                "severity": "high",
                                "line": i
                            })
                            break
            
            # Check for input validation
            if "request" in content.lower() and "validate" not in content.lower():
                # Basic check - not comprehensive
                findings["best_practices"].append({
                    "file": file_path,
                    "issue": "Consider adding input validation",
                    "severity": "low"
                })
        
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
    
    # Check for rate limiting
    rate_limiter_file = Path("app/utils/rate_limiter.py")
    if rate_limiter_file.exists():
        findings["best_practices"].append({
            "file": "app/utils/rate_limiter.py",
            "issue": "Rate limiting utility exists",
            "status": "good"
        })
    else:
        findings["recommendations"].append({
            "type": "security",
            "issue": "Rate limiting not implemented",
            "suggestion": "Add rate limiting to prevent abuse",
            "priority": "medium"
        })
    
    return findings


async def documentation_analysis_agent(task: AgentTask) -> Dict[str, Any]:
    """Analyze documentation completeness.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with documentation analysis results
    """
    gaps = {
        "missing_docs": [],
        "outdated_docs": [],
        "coverage": {}
    }
    
    # Check for required documentation
    required_docs = [
        "README.md",
        "QUICKSTART.md",
        "docs/API.md",
    ]
    
    for doc in required_docs:
        path = Path(doc)
        if not path.exists():
            gaps["missing_docs"].append(doc)
    
    # Check API documentation
    api_file = Path("app/api/jobs.py")
    if api_file.exists():
        try:
            content = api_file.read_text()
            endpoints = content.count("@router.")
            docstrings = content.count('"""')
            
            # Count function definitions
            tree = ast.parse(content)
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            
            gaps["coverage"]["api_documentation"] = {
                "endpoints": endpoints,
                "functions": len(functions),
                "docstrings": docstrings // 2,  # Rough estimate
                "coverage_pct": (docstrings / (len(functions) * 2) * 100) if functions else 0
            }
        except Exception as e:
            logger.warning(f"Error analyzing API docs: {e}")
            gaps["coverage"]["api_documentation"] = {"error": str(e)}
    
    # Check README
    readme_file = Path("README.md")
    if readme_file.exists():
        readme_content = readme_file.read_text()
        gaps["coverage"]["readme"] = {
            "exists": True,
            "length": len(readme_content),
            "has_setup": "setup" in readme_content.lower(),
            "has_api": "api" in readme_content.lower() or "endpoint" in readme_content.lower()
        }
    else:
        gaps["missing_docs"].append("README.md")
    
    return gaps


async def compliance_analysis_agent(task: AgentTask) -> Dict[str, Any]:
    """Analyze compliance with ToS and best practices.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with compliance status
    """
    compliance = {
        "tos_compliance": {},
        "rate_limiting": {},
        "data_privacy": {},
        "error_handling": {},
        "backup_procedures": {},
        "recommendations": []
    }
    
    # Check rate limiting implementation
    rate_limiter_file = Path("app/utils/rate_limiter.py")
    if rate_limiter_file.exists():
        compliance["rate_limiting"]["implemented"] = True
        try:
            content = rate_limiter_file.read_text()
            compliance["rate_limiting"]["has_delay"] = "delay" in content.lower()
        except:
            pass
    else:
        compliance["rate_limiting"]["implemented"] = False
        compliance["recommendations"].append({
            "type": "compliance",
            "issue": "Rate limiting not implemented",
            "priority": "high",
            "reason": "Required for ToS compliance with job boards"
        })
    
    # Check error handling
    error_handling_files = [
        "app/services/job_scraper.py",
        "app/api/jobs.py",
    ]
    
    error_handling_count = 0
    for file_path in error_handling_files:
        path = Path(file_path)
        if path.exists():
            try:
                content = path.read_text()
                if "try:" in content and "except" in content:
                    error_handling_count += 1
            except:
                pass
    
    compliance["error_handling"]["files_with_handling"] = error_handling_count
    compliance["error_handling"]["total_files_checked"] = len(error_handling_files)
    
    if error_handling_count < len(error_handling_files):
        compliance["recommendations"].append({
            "type": "compliance",
            "issue": "Some files lack error handling",
            "priority": "medium",
            "reason": "Error handling required for robust operation"
        })
    
    # Check data privacy (basic checks)
    db_file = Path("app/database.py")
    if db_file.exists():
        try:
            content = db_file.read_text()
            compliance["data_privacy"]["has_connection_pooling"] = "pool" in content.lower()
        except:
            pass
    
    # Check backup procedures (check for migration files)
    alembic_dir = Path("alembic/versions")
    if alembic_dir.exists():
        migration_files = list(alembic_dir.glob("*.py"))
        compliance["backup_procedures"]["has_migrations"] = len(migration_files) > 0
        compliance["backup_procedures"]["migration_count"] = len(migration_files)
    else:
        compliance["backup_procedures"]["has_migrations"] = False
        compliance["recommendations"].append({
            "type": "compliance",
            "issue": "No database migrations found",
            "priority": "medium",
            "reason": "Migrations are important for backup and rollback"
        })
    
    return compliance


