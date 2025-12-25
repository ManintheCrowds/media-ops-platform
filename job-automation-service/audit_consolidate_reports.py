"""Report Consolidation Script - Consolidate findings from all reports into a unified view."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set
from collections import defaultdict, Counter

# Base directory
BASE_DIR = Path(__file__).parent


def load_json_report(file_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON report file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e), "file": str(file_path)}


def extract_api_test_results(test_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract API test results from a test result entry."""
    if test_result.get("agent_type") != "api_test":
        return None
    
    result = test_result.get("result", {})
    return {
        "task_id": test_result.get("task_id"),
        "status": test_result.get("status"),
        "endpoints_tested": result.get("endpoints_tested", []),
        "success_count": result.get("success_count", 0),
        "failure_count": result.get("failure_count", 0),
        "success_rate": result.get("success_rate", 0.0),
        "avg_response_time": result.get("avg_response_time", 0.0),
        "status_codes": result.get("status_codes", {}),
        "errors": result.get("errors", []),
    }


def extract_matcher_test_results(test_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract matcher test results from a test result entry."""
    if test_result.get("agent_type") != "matcher_test":
        return None
    
    result = test_result.get("result", {})
    return {
        "task_id": test_result.get("task_id"),
        "status": test_result.get("status"),
        "tests_run": result.get("tests_run", 0),
        "pass_count": result.get("pass_count", 0),
        "fail_count": result.get("fail_count", 0),
        "avg_score": result.get("avg_score", 0.0),
        "test_cases": result.get("test_cases", []),
    }


def extract_scraper_test_results(test_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract scraper test results from a test result entry."""
    if test_result.get("agent_type") != "scraper_test":
        return None
    
    result = test_result.get("result", {})
    return {
        "task_id": test_result.get("task_id"),
        "status": test_result.get("status"),
        "source": result.get("source"),
        "success": result.get("success", False),
        "jobs_found": result.get("jobs_found", 0),
        "error": result.get("error"),
        "status_code": result.get("status_code"),
    }


def extract_performance_metrics(test_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract performance metrics from a test result entry."""
    metrics = {
        "task_id": test_result.get("task_id"),
        "agent_type": test_result.get("agent_type"),
        "duration_seconds": test_result.get("duration_seconds", 0.0),
        "status": test_result.get("status"),
    }
    
    result = test_result.get("result", {})
    if "avg_response_time" in result:
        metrics["avg_response_time"] = result["avg_response_time"]
    if "response_times" in result:
        metrics["response_times"] = result["response_times"]
    
    return metrics


def extract_errors(test_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract errors from a test result entry."""
    errors = []
    
    if test_result.get("error"):
        errors.append({
            "task_id": test_result.get("task_id"),
            "agent_type": test_result.get("agent_type"),
            "error": test_result.get("error"),
            "type": "task_error"
        })
    
    result = test_result.get("result", {})
    if "errors" in result:
        for error in result["errors"]:
            errors.append({
                "task_id": test_result.get("task_id"),
                "agent_type": test_result.get("agent_type"),
                "error": error,
                "type": "result_error"
            })
    
    return errors


def consolidate_agent_reports() -> Dict[str, Any]:
    """Consolidate all agent test reports."""
    reports_dir = BASE_DIR / "tests" / "agents" / "reports"
    
    consolidated = {
        "api_tests": [],
        "matcher_tests": [],
        "scraper_tests": [],
        "performance_metrics": [],
        "errors": [],
        "timeline": [],
    }
    
    # Load all JSON reports
    for json_file in reports_dir.glob("report_*.json"):
        print(f"Processing: {json_file.name}")
        report_data = load_json_report(json_file)
        
        if "error" in report_data:
            continue
        
        metadata = report_data.get("metadata", {})
        test_results = report_data.get("test_results", [])
        
        for test_result in test_results:
            # Extract API test results
            api_result = extract_api_test_results(test_result)
            if api_result:
                consolidated["api_tests"].append(api_result)
            
            # Extract matcher test results
            matcher_result = extract_matcher_test_results(test_result)
            if matcher_result:
                consolidated["matcher_tests"].append(matcher_result)
            
            # Extract scraper test results
            scraper_result = extract_scraper_test_results(test_result)
            if scraper_result:
                consolidated["scraper_tests"].append(scraper_result)
            
            # Extract performance metrics
            perf_metrics = extract_performance_metrics(test_result)
            if perf_metrics:
                consolidated["performance_metrics"].append(perf_metrics)
            
            # Extract errors
            errors = extract_errors(test_result)
            consolidated["errors"].extend(errors)
            
            # Add to timeline
            if "started_at" in test_result:
                consolidated["timeline"].append({
                    "timestamp": test_result["started_at"],
                    "task_id": test_result.get("task_id"),
                    "agent_type": test_result.get("agent_type"),
                    "status": test_result.get("status"),
                    "duration": test_result.get("duration_seconds", 0.0),
                })
    
    # Sort timeline
    consolidated["timeline"].sort(key=lambda x: x["timestamp"])
    
    return consolidated


def load_status_json() -> Dict[str, Any]:
    """Load agent status JSON file."""
    status_file = BASE_DIR / "tests" / "agents" / "status" / "status.json"
    
    if not status_file.exists():
        return {}
    
    return load_json_report(status_file)


def analyze_critical_issues(consolidated: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Analyze and identify critical issues across all reports."""
    issues = []
    
    # Analyze API test failures
    api_failures = [t for t in consolidated["api_tests"] if t.get("failure_count", 0) > 0]
    if api_failures:
        issues.append({
            "category": "API Tests",
            "severity": "high",
            "count": len(api_failures),
            "description": "API endpoint test failures detected",
            "details": api_failures
        })
    
    # Analyze matcher test failures
    matcher_failures = [t for t in consolidated["matcher_tests"] if t.get("fail_count", 0) > 0]
    if matcher_failures:
        avg_score = sum(t.get("avg_score", 0.0) for t in matcher_failures) / len(matcher_failures) if matcher_failures else 0.0
        issues.append({
            "category": "Matcher Tests",
            "severity": "high",
            "count": len(matcher_failures),
            "description": f"Matcher test failures - average score: {avg_score:.3f}",
            "details": matcher_failures
        })
    
    # Analyze scraper failures
    scraper_failures = [t for t in consolidated["scraper_tests"] if not t.get("success", True)]
    if scraper_failures:
        issues.append({
            "category": "Scraper Tests",
            "severity": "medium",
            "count": len(scraper_failures),
            "description": "Scraper test failures detected",
            "details": scraper_failures
        })
    
    # Analyze errors
    if consolidated["errors"]:
        error_types = Counter(e.get("type", "unknown") for e in consolidated["errors"])
        issues.append({
            "category": "Errors",
            "severity": "high",
            "count": len(consolidated["errors"]),
            "description": f"Errors detected: {dict(error_types)}",
            "details": consolidated["errors"][:10]  # First 10 errors
        })
    
    return issues


def generate_summary_statistics(consolidated: Dict[str, Any], status: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary statistics."""
    stats = {
        "total_api_tests": len(consolidated["api_tests"]),
        "total_matcher_tests": len(consolidated["matcher_tests"]),
        "total_scraper_tests": len(consolidated["scraper_tests"]),
        "total_errors": len(consolidated["errors"]),
        "total_timeline_entries": len(consolidated["timeline"]),
    }
    
    # API test statistics
    if consolidated["api_tests"]:
        total_endpoints = sum(t.get("success_count", 0) + t.get("failure_count", 0) for t in consolidated["api_tests"])
        total_success = sum(t.get("success_count", 0) for t in consolidated["api_tests"])
        total_failure = sum(t.get("failure_count", 0) for t in consolidated["api_tests"])
        avg_response_time = sum(t.get("avg_response_time", 0.0) for t in consolidated["api_tests"]) / len(consolidated["api_tests"])
        
        stats["api_test_stats"] = {
            "total_endpoints_tested": total_endpoints,
            "total_success": total_success,
            "total_failure": total_failure,
            "success_rate": total_success / total_endpoints if total_endpoints > 0 else 0.0,
            "avg_response_time": avg_response_time,
        }
    
    # Matcher test statistics
    if consolidated["matcher_tests"]:
        total_tests = sum(t.get("tests_run", 0) for t in consolidated["matcher_tests"])
        total_pass = sum(t.get("pass_count", 0) for t in consolidated["matcher_tests"])
        total_fail = sum(t.get("fail_count", 0) for t in consolidated["matcher_tests"])
        avg_score = sum(t.get("avg_score", 0.0) for t in consolidated["matcher_tests"]) / len(consolidated["matcher_tests"])
        
        stats["matcher_test_stats"] = {
            "total_tests": total_tests,
            "total_pass": total_pass,
            "total_fail": total_fail,
            "pass_rate": total_pass / total_tests if total_tests > 0 else 0.0,
            "avg_score": avg_score,
        }
    
    # Status statistics
    if status:
        total_tasks = len(status)
        completed = sum(1 for t in status.values() if t.get("status") == "completed")
        pending = sum(1 for t in status.values() if t.get("status") == "pending")
        failed = sum(1 for t in status.values() if t.get("status") == "failed")
        in_progress = sum(1 for t in status.values() if t.get("status") == "in_progress")
        
        stats["status_stats"] = {
            "total_tasks": total_tasks,
            "completed": completed,
            "pending": pending,
            "failed": failed,
            "in_progress": in_progress,
            "completion_rate": completed / total_tasks if total_tasks > 0 else 0.0,
        }
    
    return stats


def identify_inconsistencies(consolidated: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify inconsistencies between reports."""
    inconsistencies = []
    
    # Check for duplicate task IDs with different results
    task_results = defaultdict(list)
    for api_test in consolidated["api_tests"]:
        task_id = api_test.get("task_id")
        if task_id:
            task_results[task_id].append(api_test)
    
    for task_id, results in task_results.items():
        if len(results) > 1:
            # Check if results are consistent
            success_rates = [r.get("success_rate", 0.0) for r in results]
            if len(set(success_rates)) > 1:
                inconsistencies.append({
                    "type": "inconsistent_results",
                    "task_id": task_id,
                    "description": f"Task {task_id} has inconsistent results across reports",
                    "results": results
                })
    
    return inconsistencies


def generate_recommendations(consolidated: Dict[str, Any], issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate recommendations prioritized by frequency and severity."""
    recommendations = []
    
    # High priority: Matcher scoring issues
    matcher_issues = [i for i in issues if i["category"] == "Matcher Tests"]
    if matcher_issues:
        recommendations.append({
            "priority": "high",
            "category": "Matcher",
            "recommendation": "Review and fix skill matcher scoring algorithm - scores are too low",
            "evidence_count": len(matcher_issues),
            "estimated_effort": "4-6 hours"
        })
    
    # High priority: API endpoint failures
    api_issues = [i for i in issues if i["category"] == "API Tests"]
    if api_issues:
        recommendations.append({
            "priority": "high",
            "category": "API",
            "recommendation": "Fix failing API endpoints or update tests",
            "evidence_count": len(api_issues),
            "estimated_effort": "2-3 hours"
        })
    
    # Medium priority: Scraper failures
    scraper_issues = [i for i in issues if i["category"] == "Scraper Tests"]
    if scraper_issues:
        recommendations.append({
            "priority": "medium",
            "category": "Scrapers",
            "recommendation": "Investigate scraper failures - may be due to anti-bot measures",
            "evidence_count": len(scraper_issues),
            "estimated_effort": "3-4 hours"
        })
    
    # High priority: General errors
    error_issues = [i for i in issues if i["category"] == "Errors"]
    if error_issues:
        recommendations.append({
            "priority": "high",
            "category": "Errors",
            "recommendation": "Review and fix errors detected in test runs",
            "evidence_count": len(error_issues),
            "estimated_effort": "2-4 hours"
        })
    
    return sorted(recommendations, key=lambda x: (x["priority"] == "high", -x["evidence_count"]), reverse=True)


def main():
    """Main function to consolidate reports."""
    print("=" * 80)
    print("REPORT CONSOLIDATION GENERATOR")
    print("=" * 80)
    print()
    
    # Consolidate agent reports
    print("Consolidating agent test reports...")
    consolidated = consolidate_agent_reports()
    
    # Load status
    print("Loading agent status...")
    status = load_status_json()
    
    # Analyze critical issues
    print("Analyzing critical issues...")
    issues = analyze_critical_issues(consolidated)
    
    # Generate statistics
    print("Generating summary statistics...")
    stats = generate_summary_statistics(consolidated, status)
    
    # Identify inconsistencies
    print("Identifying inconsistencies...")
    inconsistencies = identify_inconsistencies(consolidated)
    
    # Generate recommendations
    print("Generating recommendations...")
    recommendations = generate_recommendations(consolidated, issues)
    
    # Create final consolidated report
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary_statistics": stats,
        "critical_issues": issues,
        "inconsistencies": inconsistencies,
        "recommendations": recommendations,
        "consolidated_data": {
            "api_tests": consolidated["api_tests"],
            "matcher_tests": consolidated["matcher_tests"],
            "scraper_tests": consolidated["scraper_tests"],
            "performance_metrics": consolidated["performance_metrics"],
            "errors": consolidated["errors"],
            "timeline": consolidated["timeline"],
        },
        "status": status,
    }
    
    # Save consolidated report
    output_file = BASE_DIR / "audit_reports_consolidated.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Consolidated report saved to: {output_file}")
    print()
    print("Summary:")
    print(f"  API tests: {stats.get('total_api_tests', 0)}")
    print(f"  Matcher tests: {stats.get('total_matcher_tests', 0)}")
    print(f"  Scraper tests: {stats.get('total_scraper_tests', 0)}")
    print(f"  Errors: {stats.get('total_errors', 0)}")
    print(f"  Critical issues: {len(issues)}")
    print(f"  Inconsistencies: {len(inconsistencies)}")
    print(f"  Recommendations: {len(recommendations)}")
    print()
    print("=" * 80)
    print("Consolidation complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

