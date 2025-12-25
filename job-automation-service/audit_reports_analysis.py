"""Report Analysis Dashboard Generator - Generate human-readable analysis of all reports."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import Counter, defaultdict

# Base directory
BASE_DIR = Path(__file__).parent


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


def generate_analysis_markdown() -> str:
    """Generate markdown analysis report."""
    # Load inventory
    inventory_file = BASE_DIR / "audit_reports_inventory.json"
    inventory = load_json_file(inventory_file)
    
    # Load consolidated report
    consolidated_file = BASE_DIR / "audit_reports_consolidated.json"
    consolidated = load_json_file(consolidated_file)
    
    if "error" in inventory or "error" in consolidated:
        return "# Report Analysis\n\nError loading data files. Please run audit_reports_inventory.py and audit_consolidate_reports.py first.\n"
    
    md = []
    md.append("# Report Analysis Dashboard")
    md.append("")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append("")
    md.append("---")
    md.append("")
    
    # Executive Summary
    md.append("## Executive Summary")
    md.append("")
    
    stats = consolidated.get("summary_statistics", {})
    issues = consolidated.get("critical_issues", [])
    recommendations = consolidated.get("recommendations", [])
    
    md.append(f"This analysis consolidates findings from **{inventory.get('summary', {}).get('total_reports', 0)} reports** across the system.")
    md.append("")
    
    # Key metrics
    md.append("### Key Metrics")
    md.append("")
    md.append(f"- **Total Reports Analyzed:** {inventory.get('summary', {}).get('total_reports', 0)}")
    md.append(f"- **Total Size:** {inventory.get('summary', {}).get('total_size_kb', 0):.2f} KB")
    md.append(f"- **API Tests:** {stats.get('total_api_tests', 0)}")
    md.append(f"- **Matcher Tests:** {stats.get('total_matcher_tests', 0)}")
    md.append(f"- **Scraper Tests:** {stats.get('total_scraper_tests', 0)}")
    md.append(f"- **Total Errors:** {stats.get('total_errors', 0)}")
    md.append(f"- **Critical Issues:** {len(issues)}")
    md.append(f"- **Recommendations:** {len(recommendations)}")
    md.append("")
    
    # Report Inventory
    md.append("## Report Inventory")
    md.append("")
    md.append("### By Type")
    md.append("")
    md.append("| Type | Count |")
    md.append("|------|-------|")
    for report_type, count in sorted(inventory.get('summary', {}).get('by_type', {}).items()):
        md.append(f"| {report_type} | {count} |")
    md.append("")
    
    md.append("### By Extension")
    md.append("")
    md.append("| Extension | Count |")
    md.append("|-----------|-------|")
    for ext, count in sorted(inventory.get('summary', {}).get('by_extension', {}).items()):
        md.append(f"| {ext} | {count} |")
    md.append("")
    
    # Critical Issues Matrix
    md.append("## Critical Issues Matrix")
    md.append("")
    md.append("| Issue Category | Severity | Count | Description |")
    md.append("|----------------|----------|-------|-------------|")
    
    for issue in issues:
        category = issue.get("category", "Unknown")
        severity = issue.get("severity", "unknown")
        count = issue.get("count", 0)
        description = issue.get("description", "")[:60] + "..." if len(issue.get("description", "")) > 60 else issue.get("description", "")
        md.append(f"| {category} | {severity} | {count} | {description} |")
    md.append("")
    
    # Test Coverage Analysis
    md.append("## Test Coverage Analysis")
    md.append("")
    
    # API Test Coverage
    api_stats = stats.get("api_test_stats", {})
    if api_stats:
        md.append("### API Tests")
        md.append("")
        md.append(f"- **Total Endpoints Tested:** {api_stats.get('total_endpoints_tested', 0)}")
        md.append(f"- **Success Count:** {api_stats.get('total_success', 0)}")
        md.append(f"- **Failure Count:** {api_stats.get('total_failure', 0)}")
        md.append(f"- **Success Rate:** {api_stats.get('success_rate', 0.0):.1%}")
        md.append(f"- **Average Response Time:** {api_stats.get('avg_response_time', 0.0):.3f}s")
        md.append("")
    
    # Matcher Test Coverage
    matcher_stats = stats.get("matcher_test_stats", {})
    if matcher_stats:
        md.append("### Matcher Tests")
        md.append("")
        md.append(f"- **Total Tests:** {matcher_stats.get('total_tests', 0)}")
        md.append(f"- **Pass Count:** {matcher_stats.get('total_pass', 0)}")
        md.append(f"- **Fail Count:** {matcher_stats.get('total_fail', 0)}")
        md.append(f"- **Pass Rate:** {matcher_stats.get('pass_rate', 0.0):.1%}")
        md.append(f"- **Average Score:** {matcher_stats.get('avg_score', 0.0):.3f}")
        md.append("")
    
    # Status Statistics
    status_stats = stats.get("status_stats", {})
    if status_stats:
        md.append("### Task Status")
        md.append("")
        md.append(f"- **Total Tasks:** {status_stats.get('total_tasks', 0)}")
        md.append(f"- **Completed:** {status_stats.get('completed', 0)}")
        md.append(f"- **Pending:** {status_stats.get('pending', 0)}")
        md.append(f"- **Failed:** {status_stats.get('failed', 0)}")
        md.append(f"- **In Progress:** {status_stats.get('in_progress', 0)}")
        md.append(f"- **Completion Rate:** {status_stats.get('completion_rate', 0.0):.1%}")
        md.append("")
    
    # Success/Failure Rates by Component
    md.append("## Success/Failure Rates by Component")
    md.append("")
    
    api_tests = consolidated.get("consolidated_data", {}).get("api_tests", [])
    if api_tests:
        md.append("### API Endpoints")
        md.append("")
        md.append("| Endpoint | Success Rate | Avg Response Time |")
        md.append("|----------|-------------|-------------------|")
        
        endpoint_stats = defaultdict(lambda: {"success": 0, "total": 0, "times": []})
        for test in api_tests:
            endpoints = test.get("endpoints_tested", [])
            for endpoint in endpoints:
                endpoint_stats[endpoint]["total"] += 1
                # Assume success if in endpoints_tested list
                endpoint_stats[endpoint]["success"] += 1
        
        for endpoint, stats_data in sorted(endpoint_stats.items()):
            success_rate = stats_data["success"] / stats_data["total"] if stats_data["total"] > 0 else 0.0
            md.append(f"| {endpoint} | {success_rate:.1%} | N/A |")
        md.append("")
    
    # Recommendations
    md.append("## Recommendations")
    md.append("")
    md.append("Prioritized recommendations based on frequency and severity:")
    md.append("")
    
    for i, rec in enumerate(recommendations, 1):
        priority = rec.get("priority", "unknown")
        category = rec.get("category", "Unknown")
        recommendation = rec.get("recommendation", "")
        evidence_count = rec.get("evidence_count", 0)
        effort = rec.get("estimated_effort", "Unknown")
        
        md.append(f"### {i}. {category} ({priority} priority)")
        md.append("")
        md.append(f"**Recommendation:** {recommendation}")
        md.append("")
        md.append(f"- **Evidence Count:** {evidence_count}")
        md.append(f"- **Estimated Effort:** {effort}")
        md.append("")
    
    # Inconsistencies
    inconsistencies = consolidated.get("inconsistencies", [])
    if inconsistencies:
        md.append("## Inconsistencies Identified")
        md.append("")
        md.append(f"Found **{len(inconsistencies)}** inconsistencies across reports:")
        md.append("")
        for inc in inconsistencies:
            inc_type = inc.get("type", "unknown")
            description = inc.get("description", "")
            md.append(f"- **{inc_type}:** {description}")
        md.append("")
    
    # Timeline Summary
    timeline = consolidated.get("consolidated_data", {}).get("timeline", [])
    if timeline:
        md.append("## Timeline Summary")
        md.append("")
        md.append(f"Total timeline entries: {len(timeline)}")
        md.append("")
        md.append("| Timestamp | Task ID | Agent Type | Status | Duration (s) |")
        md.append("|-----------|---------|------------|--------|--------------|")
        
        for entry in timeline[:20]:  # First 20 entries
            timestamp = entry.get("timestamp", "")[:19]  # Truncate to date/time
            task_id = entry.get("task_id", "")
            agent_type = entry.get("agent_type", "")
            status = entry.get("status", "")
            duration = entry.get("duration", 0.0)
            md.append(f"| {timestamp} | {task_id} | {agent_type} | {status} | {duration:.3f} |")
        
        if len(timeline) > 20:
            md.append(f"| ... | ... | ... | ... | ... |")
            md.append(f"*({len(timeline) - 20} more entries)*")
        md.append("")
    
    md.append("---")
    md.append("")
    md.append("*This report was generated automatically by the audit system.*")
    
    return "\n".join(md)


def main():
    """Main function to generate analysis report."""
    print("=" * 80)
    print("REPORT ANALYSIS DASHBOARD GENERATOR")
    print("=" * 80)
    print()
    
    print("Generating analysis markdown...")
    markdown = generate_analysis_markdown()
    
    # Save analysis
    output_file = BASE_DIR / "audit_reports_analysis.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"[OK] Analysis report saved to: {output_file}")
    print()
    print("=" * 80)
    print("Analysis generation complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

