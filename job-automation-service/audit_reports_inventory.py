"""Report Inventory Script - Scan and catalog all reports in the system."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import re

# Base directory
BASE_DIR = Path(__file__).parent


def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """Get metadata for a file."""
    stat = file_path.stat()
    return {
        "size_bytes": stat.st_size,
        "size_kb": round(stat.st_size / 1024, 2),
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
    }


def extract_timestamp_from_filename(filename: str) -> str:
    """Extract timestamp from report filename (format: report_YYYYMMDD_HHMMSS.*)."""
    match = re.search(r'report_(\d{8}_\d{6})', filename)
    if match:
        return match.group(1)
    return None


def classify_report_type(file_path: Path) -> str:
    """Classify the type of report based on path and content."""
    path_str = str(file_path)
    
    if "agents/reports" in path_str:
        if file_path.suffix == ".json":
            return "agent_test_json"
        elif file_path.suffix == ".md":
            return "agent_test_markdown"
    elif "agents/status" in path_str:
        return "agent_status"
    elif "docs/" in path_str:
        return "documentation"
    elif file_path.name in ["PROJECT_STATUS_REPORT.md", "CURRENT_STATUS_AUDIT.md", 
                            "DEBUG_COMPLETE.md", "IMPLEMENTATION_COMPLETE.md",
                            "TESTING_RESULTS.md"]:
        return "status_report"
    elif "jobs_inventory" in file_path.name:
        return "data_inventory"
    else:
        return "other"


def parse_json_report(file_path: Path) -> Dict[str, Any]:
    """Parse JSON report and extract key metrics."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metrics = {
            "parse_success": True,
            "has_metadata": "metadata" in data,
            "has_test_results": "test_results" in data,
        }
        
        if "metadata" in data:
            metadata = data["metadata"]
            metrics.update({
                "total_tasks": metadata.get("total_tasks", 0),
                "completed_tasks": metadata.get("completed_tasks", 0),
                "failed_tasks": metadata.get("failed_tasks", 0),
                "generated_at": metadata.get("generated_at"),
            })
        
        if "test_results" in data:
            test_results = data["test_results"]
            metrics.update({
                "test_result_count": len(test_results),
                "agent_types": list(set(r.get("agent_type", "unknown") for r in test_results)),
            })
            
            # Extract success/failure counts
            success_count = sum(1 for r in test_results if r.get("status") == "completed")
            fail_count = sum(1 for r in test_results if r.get("status") == "failed")
            metrics.update({
                "test_success_count": success_count,
                "test_fail_count": fail_count,
            })
        
        return metrics
    except Exception as e:
        return {
            "parse_success": False,
            "parse_error": str(e)
        }


def scan_reports_directory(directory: Path, pattern: str = "*") -> List[Dict[str, Any]]:
    """Scan a directory for report files."""
    reports = []
    
    if not directory.exists():
        return reports
    
    for file_path in directory.glob(pattern):
        if file_path.is_file():
            report_type = classify_report_type(file_path)
            metadata = get_file_metadata(file_path)
            timestamp = extract_timestamp_from_filename(file_path.name)
            
            report_info = {
                "file_path": str(file_path.relative_to(BASE_DIR)),
                "absolute_path": str(file_path),
                "filename": file_path.name,
                "report_type": report_type,
                "timestamp": timestamp,
                **metadata
            }
            
            # Parse JSON reports for additional metrics
            if file_path.suffix == ".json":
                metrics = parse_json_report(file_path)
                report_info["metrics"] = metrics
            
            reports.append(report_info)
    
    return reports


def scan_all_reports() -> Dict[str, Any]:
    """Scan all report locations and generate inventory."""
    inventory = {
        "generated_at": datetime.now().isoformat(),
        "base_directory": str(BASE_DIR),
        "reports": []
    }
    
    # Scan agent test reports
    agent_reports_dir = BASE_DIR / "tests" / "agents" / "reports"
    print(f"Scanning agent reports: {agent_reports_dir}")
    agent_reports = scan_reports_directory(agent_reports_dir, "report_*")
    inventory["reports"].extend(agent_reports)
    
    # Scan agent status
    agent_status_dir = BASE_DIR / "tests" / "agents" / "status"
    print(f"Scanning agent status: {agent_status_dir}")
    status_reports = scan_reports_directory(agent_status_dir, "*.json")
    inventory["reports"].extend(status_reports)
    
    # Scan documentation reports
    docs_dir = BASE_DIR / "docs"
    print(f"Scanning documentation: {docs_dir}")
    doc_reports = scan_reports_directory(docs_dir, "*.md")
    inventory["reports"].extend(doc_reports)
    
    # Scan root directory status reports
    root_dir = BASE_DIR
    status_report_files = [
        "PROJECT_STATUS_REPORT.md",
        "CURRENT_STATUS_AUDIT.md",
        "DEBUG_COMPLETE.md",
        "IMPLEMENTATION_COMPLETE.md",
        "TESTING_RESULTS.md",
        "jobs_inventory.json"
    ]
    print(f"Scanning root directory status reports")
    for filename in status_report_files:
        file_path = root_dir / filename
        if file_path.exists():
            report_type = classify_report_type(file_path)
            metadata = get_file_metadata(file_path)
            report_info = {
                "file_path": str(file_path.relative_to(BASE_DIR)),
                "absolute_path": str(file_path),
                "filename": file_path.name,
                "report_type": report_type,
                "timestamp": None,
                **metadata
            }
            
            if file_path.suffix == ".json":
                metrics = parse_json_report(file_path)
                report_info["metrics"] = metrics
            
            inventory["reports"].append(report_info)
    
    # Generate summary statistics
    inventory["summary"] = {
        "total_reports": len(inventory["reports"]),
        "by_type": {},
        "by_extension": {},
        "total_size_kb": sum(r.get("size_kb", 0) for r in inventory["reports"]),
    }
    
    for report in inventory["reports"]:
        report_type = report["report_type"]
        inventory["summary"]["by_type"][report_type] = \
            inventory["summary"]["by_type"].get(report_type, 0) + 1
        
        ext = Path(report["file_path"]).suffix
        inventory["summary"]["by_extension"][ext] = \
            inventory["summary"]["by_extension"].get(ext, 0) + 1
    
    return inventory


def main():
    """Main function to generate report inventory."""
    print("=" * 80)
    print("REPORT INVENTORY GENERATOR")
    print("=" * 80)
    print()
    
    inventory = scan_all_reports()
    
    # Save inventory to JSON
    output_file = BASE_DIR / "audit_reports_inventory.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Inventory saved to: {output_file}")
    print()
    print("Summary:")
    print(f"  Total reports: {inventory['summary']['total_reports']}")
    print(f"  Total size: {inventory['summary']['total_size_kb']:.2f} KB")
    print()
    print("By type:")
    for report_type, count in sorted(inventory['summary']['by_type'].items()):
        print(f"  {report_type}: {count}")
    print()
    print("By extension:")
    for ext, count in sorted(inventory['summary']['by_extension'].items()):
        print(f"  {ext}: {count}")
    print()
    print("=" * 80)
    print("Inventory generation complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

