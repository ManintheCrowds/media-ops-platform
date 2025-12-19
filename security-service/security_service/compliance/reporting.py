"""Compliance reporting service."""

import csv
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.security_events import SecurityEvent
from ..models.incidents import SecurityIncident
from ..models.threats import AuditLog, VulnerabilityScan, PatchStatus


class ComplianceReporter:
    """Compliance reporting with multiple framework support."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def generate_security_audit_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate security audit report."""
        # Security events
        total_events = self.db.query(SecurityEvent).filter(
            SecurityEvent.detected_at >= start_date,
            SecurityEvent.detected_at <= end_date
        ).count()
        
        events_by_type = {}
        events = self.db.query(
            SecurityEvent.event_type,
            func.count(SecurityEvent.id)
        ).filter(
            SecurityEvent.detected_at >= start_date,
            SecurityEvent.detected_at <= end_date
        ).group_by(SecurityEvent.event_type).all()
        
        for event_type, count in events:
            events_by_type[event_type] = count
        
        # Incidents
        total_incidents = self.db.query(SecurityIncident).filter(
            SecurityIncident.created_at >= start_date,
            SecurityIncident.created_at <= end_date
        ).count()
        
        resolved_incidents = self.db.query(SecurityIncident).filter(
            SecurityIncident.created_at >= start_date,
            SecurityIncident.created_at <= end_date,
            SecurityIncident.status == "resolved"
        ).count()
        
        # Vulnerabilities
        total_vulnerabilities = self.db.query(VulnerabilityScan).filter(
            VulnerabilityScan.detected_at >= start_date,
            VulnerabilityScan.detected_at <= end_date
        ).count()
        
        unresolved_vulnerabilities = self.db.query(VulnerabilityScan).filter(
            VulnerabilityScan.resolved == "false"
        ).count()
        
        # Patches
        security_patches = self.db.query(PatchStatus).filter(
            PatchStatus.is_security_patch == "true",
            PatchStatus.patch_available == "true"
        ).count()
        
        return {
            "report_type": "security_audit",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_security_events": total_events,
                "events_by_type": events_by_type,
                "total_incidents": total_incidents,
                "resolved_incidents": resolved_incidents,
                "total_vulnerabilities": total_vulnerabilities,
                "unresolved_vulnerabilities": unresolved_vulnerabilities,
                "security_patches_available": security_patches
            }
        }
    
    def generate_access_control_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate access control report."""
        # Audit logs
        total_logins = self.db.query(AuditLog).filter(
            AuditLog.event_type == "auth",
            AuditLog.action == "login",
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        ).count()
        
        failed_logins = self.db.query(AuditLog).filter(
            AuditLog.event_type == "auth",
            AuditLog.action == "login",
            AuditLog.success == "false",
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        ).count()
        
        # Admin actions
        admin_actions = self.db.query(AuditLog).filter(
            AuditLog.event_type == "admin_action",
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        ).count()
        
        return {
            "report_type": "access_control",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_logins": total_logins,
                "failed_logins": failed_logins,
                "admin_actions": admin_actions
            }
        }
    
    def export_report_csv(self, report_data: Dict[str, Any], filename: str) -> str:
        """Export report to CSV format."""
        filepath = f"/tmp/{filename}"
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(["Report Type", report_data["report_type"]])
            writer.writerow(["Generated At", report_data["generated_at"]])
            writer.writerow(["Period Start", report_data["period"]["start"]])
            writer.writerow(["Period End", report_data["period"]["end"]])
            writer.writerow([])
            
            # Write summary
            writer.writerow(["Summary"])
            for key, value in report_data["summary"].items():
                if isinstance(value, dict):
                    writer.writerow([key])
                    for sub_key, sub_value in value.items():
                        writer.writerow([f"  {sub_key}", sub_value])
                else:
                    writer.writerow([key, value])
        
        return filepath

