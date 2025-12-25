"""Audit Orchestrator - Run all audit scripts and generate master report."""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Base directory
BASE_DIR = Path(__file__).parent


def run_script(script_name: str) -> Dict[str, Any]:
    """Run an audit script and return results."""
    result = {
        "script": script_name,
        "status": "pending",
        "output_file": None,
        "error": None
    }
    
    script_path = BASE_DIR / script_name
    
    if not script_path.exists():
        result["status"] = "fail"
        result["error"] = f"Script not found: {script_name}"
        return result
    
    try:
        print(f"Running: {script_name}...")
        process = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if process.returncode == 0:
            result["status"] = "success"
            result["stdout"] = process.stdout
        else:
            result["status"] = "fail"
            result["error"] = process.stderr
            result["stdout"] = process.stdout
            
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = "Script execution timed out"
    except Exception as e:
        result["status"] = "fail"
        result["error"] = str(e)
    
    return result


def load_json_report(file_path: Path) -> Dict[str, Any]:
    """Load a JSON report file."""
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def generate_master_report(all_results: Dict[str, Any]) -> str:
    """Generate master audit report markdown."""
    
    md = []
    md.append("# Master Audit Report")
    md.append("")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append("")
    md.append("---")
    md.append("")
    
    # Executive Summary
    md.append("## Executive Summary")
    md.append("")
    
    script_results = all_results.get("script_results", {})
    successful_scripts = sum(1 for r in script_results.values() if r.get("status") == "success")
    total_scripts = len(script_results)
    
    md.append(f"This comprehensive audit analyzed the job automation system through **{total_scripts} audit scripts**.")
    md.append(f"**{successful_scripts} scripts** completed successfully.")
    md.append("")
    
    # Overall System Health
    md.append("### Overall System Health")
    md.append("")
    
    # Load reports to assess health
    stages_report = load_json_report(BASE_DIR / "audit_pipeline_stages_report.json")
    e2e_report = load_json_report(BASE_DIR / "audit_pipeline_e2e_report.json")
    data_flow_report = load_json_report(BASE_DIR / "audit_pipeline_data_flow_report.json")
    consolidated_report = load_json_report(BASE_DIR / "audit_reports_consolidated.json")
    
    # Pipeline health
    stages_summary = stages_report.get("summary", {})
    if stages_summary:
        md.append(f"- **Pipeline Stages:** {stages_summary.get('passed', 0)}/{stages_summary.get('total_stages', 0)} passed ({stages_summary.get('pass_rate', 0.0):.1%})")
    
    # E2E health
    e2e_summary = e2e_report.get("summary", {})
    if e2e_summary:
        md.append(f"- **E2E Tests:** {e2e_summary.get('passed', 0)}/{e2e_summary.get('total_tests', 0)} passed ({e2e_summary.get('pass_rate', 0.0):.1%})")
    
    # Data flow health
    data_flow_summary = data_flow_report.get("summary", {})
    if data_flow_summary:
        md.append(f"- **Data Flow Checks:** {data_flow_summary.get('passed', 0)}/{data_flow_summary.get('total_checks', 0)} passed ({data_flow_summary.get('pass_rate', 0.0):.1%})")
    
    md.append("")
    
    # Critical Issues
    md.append("### Critical Issues Summary")
    md.append("")
    
    if consolidated_report:
        issues = consolidated_report.get("critical_issues", [])
        if issues:
            md.append(f"Found **{len(issues)} critical issues** across all reports:")
            md.append("")
            for issue in issues[:5]:  # Top 5
                md.append(f"- **{issue.get('category', 'Unknown')}** ({issue.get('severity', 'unknown')}): {issue.get('description', '')}")
            md.append("")
        else:
            md.append("No critical issues identified.")
            md.append("")
    
    # Recommendations
    md.append("### Recommendations Priority")
    md.append("")
    
    if consolidated_report:
        recommendations = consolidated_report.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations[:5], 1):  # Top 5
                priority = rec.get("priority", "unknown")
                category = rec.get("category", "Unknown")
                recommendation = rec.get("recommendation", "")
                effort = rec.get("estimated_effort", "Unknown")
                md.append(f"{i}. **{category}** ({priority} priority) - {recommendation} - *Effort: {effort}*")
            md.append("")
        else:
            md.append("No recommendations generated.")
            md.append("")
    
    # Reports Audit Results
    md.append("## Reports Audit Results")
    md.append("")
    md.append("### Report Inventory")
    md.append("")
    
    inventory = load_json_report(BASE_DIR / "audit_reports_inventory.json")
    if inventory:
        summary = inventory.get("summary", {})
        md.append(f"- **Total Reports:** {summary.get('total_reports', 0)}")
        md.append(f"- **Total Size:** {summary.get('total_size_kb', 0):.2f} KB")
        md.append("")
        md.append("**By Type:**")
        for report_type, count in sorted(summary.get('by_type', {}).items()):
            md.append(f"- {report_type}: {count}")
        md.append("")
    
    md.append("### Consolidated Findings")
    md.append("")
    
    if consolidated_report:
        stats = consolidated_report.get("summary_statistics", {})
        md.append(f"- **API Tests:** {stats.get('total_api_tests', 0)}")
        md.append(f"- **Matcher Tests:** {stats.get('total_matcher_tests', 0)}")
        md.append(f"- **Scraper Tests:** {stats.get('total_scraper_tests', 0)}")
        md.append(f"- **Total Errors:** {stats.get('total_errors', 0)}")
        md.append("")
    
    # Pipeline Audit Results
    md.append("## Pipeline Audit Results")
    md.append("")
    
    md.append("### Stage-by-Stage Verification")
    md.append("")
    
    if stages_report:
        md.append("| Stage | Status |")
        md.append("|-------|--------|")
        for stage in stages_report.get("stages", []):
            stage_name = stage.get("stage", "Unknown")
            status = stage.get("overall_status", "unknown")
            md.append(f"| {stage_name} | {status} |")
        md.append("")
    
    md.append("### Data Flow Validation")
    md.append("")
    
    if data_flow_report:
        md.append("| Check | Status |")
        md.append("|-------|--------|")
        for validation in data_flow_report.get("validations", []):
            check_name = validation.get("check", "Unknown")
            status = validation.get("status", "unknown")
            md.append(f"| {check_name} | {status} |")
        md.append("")
    
    md.append("### End-to-End Test Results")
    md.append("")
    
    if e2e_report:
        md.append("| Test Scenario | Status |")
        md.append("|---------------|--------|")
        for test in e2e_report.get("test_scenarios", []):
            test_name = test.get("test_name", "Unknown")
            status = test.get("status", "unknown")
            md.append(f"| {test_name} | {status} |")
        md.append("")
    
    # Gap Analysis
    md.append("## Gap Analysis")
    md.append("")
    
    # Identify gaps from reports
    gaps = []
    
    if stages_report:
        for stage in stages_report.get("stages", []):
            if stage.get("overall_status") == "fail":
                gaps.append(f"Stage failure: {stage.get('stage', 'Unknown')}")
    
    if e2e_report:
        for test in e2e_report.get("test_scenarios", []):
            if test.get("status") == "fail":
                gaps.append(f"E2E test failure: {test.get('test_name', 'Unknown')}")
    
    if gaps:
        md.append("### Missing Functionality")
        md.append("")
        for gap in gaps:
            md.append(f"- {gap}")
        md.append("")
    else:
        md.append("No significant gaps identified.")
        md.append("")
    
    # Action Items
    md.append("## Action Items")
    md.append("")
    
    if consolidated_report:
        recommendations = consolidated_report.get("recommendations", [])
        if recommendations:
            md.append("Prioritized action items based on audit findings:")
            md.append("")
            for i, rec in enumerate(recommendations, 1):
                priority = rec.get("priority", "unknown")
                category = rec.get("category", "Unknown")
                recommendation = rec.get("recommendation", "")
                effort = rec.get("estimated_effort", "Unknown")
                evidence = rec.get("evidence_count", 0)
                md.append(f"{i}. **[{priority.upper()}]** {category}: {recommendation}")
                md.append(f"   - Evidence: {evidence} reports")
                md.append(f"   - Estimated effort: {effort}")
                md.append("")
        else:
            md.append("No action items identified.")
            md.append("")
    
    # Script Execution Summary
    md.append("## Script Execution Summary")
    md.append("")
    md.append("| Script | Status |")
    md.append("|--------|--------|")
    for script_name, result in script_results.items():
        status = result.get("status", "unknown")
        md.append(f"| {script_name} | {status} |")
    md.append("")
    
    md.append("---")
    md.append("")
    md.append("*This report was generated automatically by the comprehensive audit system.*")
    
    return "\n".join(md)


def main():
    """Main function to run all audits and generate master report."""
    print("=" * 80)
    print("COMPREHENSIVE SYSTEM AUDIT - ORCHESTRATOR")
    print("=" * 80)
    print()
    
    all_results = {
        "generated_at": datetime.now().isoformat(),
        "script_results": {}
    }
    
    # Define audit scripts in order
    audit_scripts = [
        "audit_reports_inventory.py",
        "audit_consolidate_reports.py",
        "audit_reports_analysis.py",
        "audit_pipeline_diagram.py",
        "audit_pipeline_stages.py",
        "audit_pipeline_e2e.py",
        "audit_pipeline_data_flow.py",
    ]
    
    # Run all scripts
    for script in audit_scripts:
        result = run_script(script)
        all_results["script_results"][script] = result
        
        if result["status"] == "success":
            print(f"  [OK] {script}")
        else:
            print(f"  [FAIL] {script}: {result.get('error', 'Unknown error')}")
    
    print()
    
    # Generate master report
    print("Generating master audit report...")
    master_report = generate_master_report(all_results)
    
    # Save master report
    output_file = BASE_DIR / "AUDIT_REPORT_MASTER.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(master_report)
    
    print(f"[OK] Master report saved to: {output_file}")
    print()
    
    # Summary
    successful = sum(1 for r in all_results["script_results"].values() if r.get("status") == "success")
    total = len(all_results["script_results"])
    
    print("=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Scripts executed: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print()
    print("=" * 80)
    print("Comprehensive audit complete!")
    print("=" * 80)
    print()
    print(f"Review the master report: {output_file}")


if __name__ == "__main__":
    main()

