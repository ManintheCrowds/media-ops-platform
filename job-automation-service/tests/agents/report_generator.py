"""Report generator for agent results."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.agent_task import AgentTask
from tests.agents.config import config

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate reports from agent execution results."""
    
    def __init__(self, output_dir: Path = None):
        """Initialize report generator.
        
        Args:
            output_dir: Output directory for reports (defaults to config)
        """
        self.output_dir = output_dir or config.report_output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def generate_reports(self) -> Dict[str, Path]:
        """Generate both Markdown and JSON reports.
        
        Returns:
            Dictionary with 'markdown' and 'json' keys pointing to report files
        """
        # Get all completed tasks
        db = SessionLocal()
        try:
            tasks = db.query(AgentTask).filter(
                AgentTask.status.in_(["completed", "failed"])
            ).all()
            
            # Organize tasks by type
            test_tasks = [t for t in tasks if t.agent_type.endswith("_test")]
            analysis_tasks = [t for t in tasks if not t.agent_type.endswith("_test")]
            
            # Generate reports
            markdown_path = self._generate_markdown_report(tasks, test_tasks, analysis_tasks)
            json_path = self._generate_json_report(tasks, test_tasks, analysis_tasks)
            
            return {
                "markdown": markdown_path,
                "json": json_path
            }
        finally:
            db.close()
    
    def _generate_markdown_report(
        self,
        all_tasks: List[AgentTask],
        test_tasks: List[AgentTask],
        analysis_tasks: List[AgentTask]
    ) -> Path:
        """Generate Markdown report."""
        report_path = self.output_dir / f"report_{self.timestamp}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            # Header
            f.write("# Job Automation Service - Test & Gap Analysis Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            completed = len([t for t in all_tasks if t.status == "completed"])
            failed = len([t for t in all_tasks if t.status == "failed"])
            total = len(all_tasks)
            
            f.write(f"- **Total Tasks:** {total}\n")
            f.write(f"- **Completed:** {completed} ({completed/total*100:.1f}%)\n")
            f.write(f"- **Failed:** {failed} ({failed/total*100:.1f}%)\n")
            f.write(f"- **Pending/Blocked:** {total - completed - failed}\n\n")
            
            # Test Results
            f.write("## Test Results\n\n")
            for task in test_tasks:
                f.write(f"### {task.description}\n\n")
                f.write(f"- **Status:** {task.status}\n")
                f.write(f"- **Agent Type:** {task.agent_type}\n")
                
                if task.started_at:
                    f.write(f"- **Started:** {task.started_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
                if task.completed_at:
                    duration = (task.completed_at - task.started_at).total_seconds() if task.started_at else 0
                    f.write(f"- **Duration:** {duration:.2f}s\n")
                
                if task.result:
                    f.write(f"- **Results:**\n")
                    f.write("```json\n")
                    f.write(json.dumps(task.result, indent=2))
                    f.write("\n```\n")
                
                if task.error:
                    f.write(f"- **Error:** {task.error}\n")
                
                f.write("\n")
            
            # Gap Analysis
            f.write("## Gap Analysis\n\n")
            gap_task = next((t for t in analysis_tasks if t.agent_type == "gap_analysis"), None)
            if gap_task and gap_task.result:
                gaps = gap_task.result
                
                if gaps.get("missing_features"):
                    f.write("### Missing Features\n\n")
                    for feature in gaps["missing_features"]:
                        f.write(f"- **{feature.get('feature', 'Unknown')}** ({feature.get('priority', 'unknown')}): {feature.get('reason', 'No reason provided')}\n")
                    f.write("\n")
                
                if gaps.get("api_coverage"):
                    f.write("### API Coverage\n\n")
                    for endpoint, status in gaps["api_coverage"].items():
                        exists = status.get("exists", False)
                        status_icon = "[OK]" if exists else "[MISSING]"
                        f.write(f"- {status_icon} `{endpoint}` - Status: {status.get('status_code', 'N/A')}\n")
                    f.write("\n")
            
            # Performance Analysis
            f.write("## Performance Analysis\n\n")
            perf_task = next((t for t in analysis_tasks if t.agent_type == "performance_analysis"), None)
            if perf_task and perf_task.result:
                perf = perf_task.result
                
                if perf.get("endpoint_performance"):
                    f.write("### Endpoint Performance\n\n")
                    f.write("| Endpoint | Avg (ms) | Min (ms) | Max (ms) | Success Rate |\n")
                    f.write("|----------|----------|----------|----------|--------------|\n")
                    
                    for endpoint, metrics in perf["endpoint_performance"].items():
                        if isinstance(metrics, dict) and "avg_ms" in metrics:
                            f.write(f"| `{endpoint}` | {metrics['avg_ms']:.2f} | {metrics['min_ms']:.2f} | {metrics['max_ms']:.2f} | {metrics.get('success_rate', 0)*100:.1f}% |\n")
                    f.write("\n")
                
                if perf.get("recommendations"):
                    f.write("### Performance Recommendations\n\n")
                    for rec in perf["recommendations"]:
                        f.write(f"- **{rec.get('endpoint', 'Unknown')}**: {rec.get('issue', '')} - {rec.get('suggestion', '')}\n")
                    f.write("\n")
            
            # Security Analysis
            f.write("## Security Analysis\n\n")
            sec_task = next((t for t in analysis_tasks if t.agent_type == "security_analysis"), None)
            if sec_task and sec_task.result:
                sec = sec_task.result
                
                if sec.get("vulnerabilities"):
                    f.write("### Vulnerabilities\n\n")
                    for vuln in sec["vulnerabilities"]:
                        severity = vuln.get("severity", "unknown").upper()
                        f.write(f"- **{severity}**: {vuln.get('issue', '')} in `{vuln.get('file', '')}`\n")
                    f.write("\n")
                
                if sec.get("recommendations"):
                    f.write("### Security Recommendations\n\n")
                    for rec in sec["recommendations"]:
                        f.write(f"- **{rec.get('priority', 'unknown')}**: {rec.get('issue', '')} - {rec.get('suggestion', '')}\n")
                    f.write("\n")
            
            # Documentation Analysis
            f.write("## Documentation Analysis\n\n")
            doc_task = next((t for t in analysis_tasks if t.agent_type == "doc_analysis"), None)
            if doc_task and doc_task.result:
                doc = doc_task.result
                
                if doc.get("missing_docs"):
                    f.write("### Missing Documentation\n\n")
                    for missing in doc["missing_docs"]:
                        f.write(f"- `{missing}`\n")
                    f.write("\n")
                
                if doc.get("coverage"):
                    f.write("### Documentation Coverage\n\n")
                    if "api_documentation" in doc["coverage"]:
                        api_cov = doc["coverage"]["api_documentation"]
                        f.write(f"- **API Documentation Coverage:** {api_cov.get('coverage_pct', 0):.1f}%\n")
                        f.write(f"  - Endpoints: {api_cov.get('endpoints', 0)}\n")
                        f.write(f"  - Functions: {api_cov.get('functions', 0)}\n")
                        f.write(f"  - Docstrings: {api_cov.get('docstrings', 0)}\n")
                    f.write("\n")
            
            # Compliance Analysis
            f.write("## Compliance Analysis\n\n")
            comp_task = next((t for t in analysis_tasks if t.agent_type == "compliance_analysis"), None)
            if comp_task and comp_task.result:
                comp = comp_task.result
                
                f.write("### Compliance Status\n\n")
                if comp.get("rate_limiting"):
                    rl = comp["rate_limiting"]
                    status = "[OK]" if rl.get("implemented") else "[MISSING]"
                    f.write(f"- **Rate Limiting:** {status} {'(Implemented)' if rl.get('implemented') else '(Not Implemented)'}\n")
                
                if comp.get("backup_procedures"):
                    bp = comp["backup_procedures"]
                    status = "[OK]" if bp.get("has_migrations") else "[MISSING]"
                    f.write(f"- **Database Migrations:** {status} ({bp.get('migration_count', 0)} migrations)\n")
                
                if comp.get("recommendations"):
                    f.write("\n### Compliance Recommendations\n\n")
                    for rec in comp["recommendations"]:
                        priority = rec.get("priority", "unknown").upper()
                        f.write(f"- **{priority}**: {rec.get('issue', '')} - {rec.get('reason', '')}\n")
                    f.write("\n")
            
            # Recommendations Summary
            f.write("## Recommendations Summary\n\n")
            all_recommendations = []
            
            for task in analysis_tasks:
                if task.result and isinstance(task.result, dict):
                    recs = task.result.get("recommendations", [])
                    all_recommendations.extend(recs)
            
            # Group by priority
            high_priority = [r for r in all_recommendations if r.get("priority", "").lower() == "high"]
            medium_priority = [r for r in all_recommendations if r.get("priority", "").lower() == "medium"]
            low_priority = [r for r in all_recommendations if r.get("priority", "").lower() == "low"]
            
            if high_priority:
                f.write("### High Priority\n\n")
                for rec in high_priority:
                    f.write(f"- {rec.get('issue', '')} - {rec.get('suggestion', '')}\n")
                f.write("\n")
            
            if medium_priority:
                f.write("### Medium Priority\n\n")
                for rec in medium_priority:
                    f.write(f"- {rec.get('issue', '')} - {rec.get('suggestion', '')}\n")
                f.write("\n")
            
            if low_priority:
                f.write("### Low Priority\n\n")
                for rec in low_priority:
                    f.write(f"- {rec.get('issue', '')} - {rec.get('suggestion', '')}\n")
                f.write("\n")
            
            # Footer
            f.write("---\n\n")
            f.write(f"*Report generated by Multi-Agent Testing Framework*\n")
        
        logger.info(f"Markdown report generated: {report_path}")
        return report_path
    
    def _generate_json_report(
        self,
        all_tasks: List[AgentTask],
        test_tasks: List[AgentTask],
        analysis_tasks: List[AgentTask]
    ) -> Path:
        """Generate JSON report."""
        report_path = self.output_dir / f"report_{self.timestamp}.json"
        
        report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "timestamp": self.timestamp,
                "total_tasks": len(all_tasks),
                "completed_tasks": len([t for t in all_tasks if t.status == "completed"]),
                "failed_tasks": len([t for t in all_tasks if t.status == "failed"]),
            },
            "test_results": [
                {
                    "task_id": task.id,
                    "agent_type": task.agent_type,
                    "description": task.description,
                    "status": task.status,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "duration_seconds": (
                        (task.completed_at - task.started_at).total_seconds()
                        if task.started_at and task.completed_at else None
                    ),
                    "result": task.result,
                    "error": task.error,
                }
                for task in test_tasks
            ],
            "analysis_results": [
                {
                    "task_id": task.id,
                    "agent_type": task.agent_type,
                    "description": task.description,
                    "status": task.status,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "result": task.result,
                    "error": task.error,
                }
                for task in analysis_tasks
            ],
            "summary": {
                "test_success_rate": (
                    len([t for t in test_tasks if t.status == "completed"]) / len(test_tasks)
                    if test_tasks else 0
                ),
                "analysis_success_rate": (
                    len([t for t in analysis_tasks if t.status == "completed"]) / len(analysis_tasks)
                    if analysis_tasks else 0
                ),
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"JSON report generated: {report_path}")
        return report_path


