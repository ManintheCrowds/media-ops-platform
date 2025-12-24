"""Analyze debug logs for recent job search activity."""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

DEBUG_LOG_PATH = Path("C:/Users/artin/software/.cursor/debug.log")

def parse_log_file() -> List[Dict]:
    """Parse the debug log file."""
    if not DEBUG_LOG_PATH.exists():
        print(f"[ERROR] Debug log not found: {DEBUG_LOG_PATH}")
        return []
    
    entries = []
    try:
        with open(DEBUG_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"[ERROR] Failed to read log file: {e}")
        return []
    
    return entries

def analyze_logs(entries: List[Dict]) -> Dict:
    """Analyze log entries for job search activity."""
    analysis = {
        "total_entries": len(entries),
        "by_hypothesis": defaultdict(int),
        "by_location": defaultdict(int),
        "searches": [],
        "errors": [],
        "jobs_found": [],
        "sources_tested": set(),
        "successful_searches": 0,
        "failed_searches": 0,
        "total_jobs_found": 0,
        "recent_activity": []
    }
    
    # Filter for job search related entries
    search_entries = [
        e for e in entries
        if "jobs.py" in e.get("location", "") or 
           "job" in e.get("message", "").lower() or
           "search" in e.get("message", "").lower() or
           e.get("hypothesisId", "").startswith("H")
    ]
    
    for entry in search_entries:
        hypothesis = entry.get("hypothesisId", "unknown")
        location = entry.get("location", "unknown")
        message = entry.get("message", "")
        data = entry.get("data", {})
        timestamp = entry.get("timestamp", 0)
        
        analysis["by_hypothesis"][hypothesis] += 1
        analysis["by_location"][location] += 1
        
        # Track searches
        if "search" in message.lower() and "start" in message.lower():
            analysis["searches"].append({
                "timestamp": timestamp,
                "location": location,
                "data": data,
                "message": message
            })
            if data.get("sources"):
                analysis["sources_tested"].update(data["sources"])
        
        # Track jobs found
        if "jobs_found" in data or "total_jobs_found" in data:
            jobs_count = data.get("jobs_found") or data.get("total_jobs_found", 0)
            analysis["jobs_found"].append({
                "timestamp": timestamp,
                "count": jobs_count,
                "sources": data.get("sources_searched", []),
                "location": location
            })
            analysis["total_jobs_found"] += jobs_count
            if jobs_count > 0:
                analysis["successful_searches"] += 1
            else:
                analysis["failed_searches"] += 1
        
        # Track errors
        if "error" in message.lower() or "ERROR" in hypothesis or "exception" in message.lower():
            analysis["errors"].append({
                "timestamp": timestamp,
                "hypothesis": hypothesis,
                "location": location,
                "message": message,
                "error_type": data.get("error_type"),
                "error_message": data.get("error_message")
            })
        
        # Recent activity (last 24 hours worth)
        if timestamp > 0:
            entry_time = datetime.fromtimestamp(timestamp / 1000)
            hours_ago = (datetime.now() - entry_time).total_seconds() / 3600
            if hours_ago < 24:
                analysis["recent_activity"].append({
                    "hours_ago": round(hours_ago, 2),
                    "hypothesis": hypothesis,
                    "message": message,
                    "data": data
                })
    
    analysis["sources_tested"] = list(analysis["sources_tested"])
    analysis["recent_activity"].sort(key=lambda x: x["hours_ago"])
    
    return analysis

def print_analysis(analysis: Dict):
    """Print formatted analysis."""
    print("=" * 60)
    print("DEBUG LOG ANALYSIS")
    print("=" * 60)
    print()
    
    print(f"Total Log Entries: {analysis['total_entries']}")
    print()
    
    print("Activity by Hypothesis ID:")
    for hyp, count in sorted(analysis["by_hypothesis"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {hyp}: {count}")
    print()
    
    print("Sources Tested:")
    if analysis["sources_tested"]:
        for source in analysis["sources_tested"]:
            print(f"  - {source}")
    else:
        print("  (none found in logs)")
    print()
    
    print("Search Statistics:")
    print(f"  Total Searches: {len(analysis['searches'])}")
    print(f"  Successful: {analysis['successful_searches']}")
    print(f"  Failed: {analysis['failed_searches']}")
    print(f"  Total Jobs Found: {analysis['total_jobs_found']}")
    print()
    
    if analysis["jobs_found"]:
        print("Recent Job Finds:")
        for find in analysis["jobs_found"][-10:]:  # Last 10
            timestamp = find["timestamp"]
            if timestamp:
                dt = datetime.fromtimestamp(timestamp / 1000)
                print(f"  {dt.strftime('%Y-%m-%d %H:%M:%S')}: {find['count']} jobs from {find['sources']}")
        print()
    
    if analysis["errors"]:
        print("Recent Errors:")
        for error in analysis["errors"][-10:]:  # Last 10
            timestamp = error["timestamp"]
            if timestamp:
                dt = datetime.fromtimestamp(timestamp / 1000)
                print(f"  {dt.strftime('%Y-%m-%d %H:%M:%S')}: {error['error_type']} - {error['error_message']}")
                print(f"    Location: {error['location']}")
        print()
    
    if analysis["recent_activity"]:
        print("Recent Activity (Last 24 Hours):")
        for activity in analysis["recent_activity"][-20:]:  # Last 20
            print(f"  {activity['hours_ago']:.1f}h ago: [{activity['hypothesis']}] {activity['message']}")
            if activity['data'].get('jobs_found'):
                print(f"    Jobs found: {activity['data']['jobs_found']}")
            if activity['data'].get('sources_searched'):
                print(f"    Sources: {activity['data']['sources_searched']}")
        print()

def main():
    """Main function."""
    print("Analyzing Debug Logs...")
    print()
    
    entries = parse_log_file()
    if not entries:
        print("[WARNING] No log entries found")
        return
    
    analysis = analyze_logs(entries)
    print_analysis(analysis)
    
    # Export to JSON
    export_data = {
        "analysis": analysis,
        "summary": {
            "total_entries": analysis["total_entries"],
            "total_jobs_found": analysis["total_jobs_found"],
            "successful_searches": analysis["successful_searches"],
            "failed_searches": analysis["failed_searches"],
            "sources_tested": analysis["sources_tested"]
        }
    }
    
    with open("debug_log_analysis.json", "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, default=str)
    
    print(f"[OK] Exported analysis to debug_log_analysis.json")

if __name__ == "__main__":
    main()

