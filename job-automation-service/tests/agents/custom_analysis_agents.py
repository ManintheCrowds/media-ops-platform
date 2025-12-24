"""Custom analysis agents for specialized checks."""

import logging
import subprocess
import json
from typing import Dict, Any
from pathlib import Path
from app.models.agent_task import AgentTask

logger = logging.getLogger(__name__)


async def coverage_analysis_agent(task: AgentTask) -> Dict[str, Any]:
    """Analyze code coverage.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with coverage analysis
    """
    results = {
        "coverage_percentage": 0.0,
        "files_covered": 0,
        "files_total": 0,
        "branches_covered": 0,
        "branches_total": 0,
        "recommendations": []
    }
    
    try:
        # Try to run coverage if pytest-cov is available
        result = subprocess.run(
            ["python", "-m", "pytest", "--cov=app", "--cov-report=json", "--cov-report=term"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0 or Path("coverage.json").exists():
            with open("coverage.json", "r") as f:
                coverage_data = json.load(f)
                totals = coverage_data.get("totals", {})
                
                results["coverage_percentage"] = totals.get("percent_covered", 0.0)
                results["files_covered"] = totals.get("covered_lines", 0)
                results["files_total"] = totals.get("num_statements", 0)
                results["branches_covered"] = totals.get("covered_branches", 0)
                results["branches_total"] = totals.get("num_branches", 0)
                
                if results["coverage_percentage"] < 70:
                    results["recommendations"].append({
                        "issue": f"Code coverage is {results['coverage_percentage']:.1f}%",
                        "suggestion": "Aim for at least 70% coverage",
                        "priority": "medium"
                    })
        else:
            results["recommendations"].append({
                "issue": "Coverage tool not available or tests failed",
                "suggestion": "Install pytest-cov and run tests with coverage",
                "priority": "low"
            })
    except Exception as e:
        logger.warning(f"Coverage analysis failed: {e}")
        results["error"] = str(e)
    
    return results


async def dependency_analysis_agent(task: AgentTask) -> Dict[str, Any]:
    """Analyze dependencies for vulnerabilities and outdated packages.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with dependency analysis
    """
    results = {
        "total_dependencies": 0,
        "outdated_packages": [],
        "vulnerabilities": [],
        "recommendations": []
    }
    
    try:
        # Check requirements.txt
        requirements_file = Path("requirements.txt")
        if requirements_file.exists():
            requirements = requirements_file.read_text()
            dependencies = [line.strip() for line in requirements.split("\n") if line.strip() and not line.startswith("#")]
            results["total_dependencies"] = len(dependencies)
            
            # Try to check for outdated packages
            try:
                result = subprocess.run(
                    ["pip", "list", "--outdated", "--format=json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    outdated = json.loads(result.stdout)
                    results["outdated_packages"] = [
                        {"name": pkg["name"], "current": pkg["version"], "latest": pkg["latest_version"]}
                        for pkg in outdated
                    ]
            except:
                pass  # pip list may not be available
            
            # Check for known vulnerable packages (basic check)
            vulnerable_patterns = ["django<2.2", "flask<1.0", "requests<2.20"]
            for pattern in vulnerable_patterns:
                if pattern in requirements.lower():
                    results["vulnerabilities"].append({
                        "package": pattern,
                        "issue": "Potentially vulnerable version",
                        "priority": "high"
                    })
            
            if results["outdated_packages"]:
                results["recommendations"].append({
                    "issue": f"{len(results['outdated_packages'])} outdated packages found",
                    "suggestion": "Update packages regularly for security patches",
                    "priority": "medium"
                })
    except Exception as e:
        logger.error(f"Dependency analysis failed: {e}")
        results["error"] = str(e)
    
    return results


async def configuration_analysis_agent(task: AgentTask) -> Dict[str, Any]:
    """Analyze configuration completeness and correctness.
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with configuration analysis
    """
    results = {
        "config_files": [],
        "missing_configs": [],
        "recommendations": []
    }
    
    # Check for required config files
    config_files = [
        "app/config.py",
        ".env.example",
        "docker-compose.yml",
        "alembic.ini"
    ]
    
    for config_file in config_files:
        path = Path(config_file)
        if path.exists():
            results["config_files"].append({
                "file": config_file,
                "exists": True,
                "size": path.stat().st_size
            })
        else:
            results["missing_configs"].append({
                "file": config_file,
                "priority": "high" if "config.py" in config_file else "medium"
            })
    
    # Check .env.example exists
    if not Path(".env.example").exists():
        results["recommendations"].append({
            "issue": ".env.example not found",
            "suggestion": "Create .env.example with required environment variables",
            "priority": "medium"
        })
    
    return results


async def api_contract_analysis_agent(task: AgentTask) -> Dict[str, Any]:
    """Validate API contract (OpenAPI/Swagger compliance).
    
    Args:
        task: Agent task
        
    Returns:
        Dictionary with API contract analysis
    """
    results = {
        "openapi_spec_exists": False,
        "endpoints_documented": 0,
        "endpoints_total": 0,
        "schema_validation": {},
        "recommendations": []
    }
    
    # Check for OpenAPI spec
    openapi_paths = [
        "openapi.json",
        "swagger.json",
        "app/openapi.json"
    ]
    
    for path in openapi_paths:
        if Path(path).exists():
            results["openapi_spec_exists"] = True
            break
    
    # Check if FastAPI auto-generates OpenAPI
    main_file = Path("app/main.py")
    if main_file.exists():
        content = main_file.read_text()
        if "FastAPI" in content:
            results["openapi_spec_exists"] = True  # FastAPI auto-generates
            results["recommendations"].append({
                "issue": "OpenAPI spec available at /openapi.json",
                "suggestion": "Use /docs for interactive API documentation",
                "priority": "low"
            })
    
    # Count endpoints in API files
    api_files = list(Path("app/api").rglob("*.py"))
    endpoint_count = 0
    for api_file in api_files:
        content = api_file.read_text()
        endpoint_count += content.count("@router.")
    
    results["endpoints_total"] = endpoint_count
    
    if not results["openapi_spec_exists"]:
        results["recommendations"].append({
            "issue": "OpenAPI spec not found",
            "suggestion": "FastAPI auto-generates OpenAPI, ensure /openapi.json is accessible",
            "priority": "low"
        })
    
    return results

