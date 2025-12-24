"""Incident management service."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..models.incidents import SecurityIncident, IncidentStatus, IncidentSeverity


class IncidentManager:
    """Incident management and tracking."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def create_incident(self, incident_type: str, severity: str, title: str,
                       description: str, source_ips: Optional[List[str]] = None,
                       related_event_ids: Optional[List[int]] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> SecurityIncident:
        """Create a new security incident."""
        incident = SecurityIncident(
            incident_type=incident_type,
            severity=severity,
            status=IncidentStatus.OPEN.value,
            title=title,
            description=description,
            source_ips=source_ips or [],
            related_event_ids=related_event_ids or [],
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        
        return incident
    
    def get_incident(self, incident_id: int) -> Optional[SecurityIncident]:
        """Get incident by ID."""
        return self.db.query(SecurityIncident).filter(
            SecurityIncident.id == incident_id
        ).first()
    
    def get_active_incidents(self, severity: Optional[str] = None) -> List[SecurityIncident]:
        """Get all active incidents."""
        query = self.db.query(SecurityIncident).filter(
            SecurityIncident.status.in_([
                IncidentStatus.OPEN.value,
                IncidentStatus.INVESTIGATING.value,
                IncidentStatus.CONTAINED.value
            ])
        )
        
        if severity:
            query = query.filter(SecurityIncident.severity == severity)
        
        return query.order_by(SecurityIncident.created_at.desc()).all()
    
    def update_incident_status(self, incident_id: int, status: str,
                              assigned_to: Optional[str] = None,
                              resolution_notes: Optional[str] = None) -> bool:
        """Update incident status."""
        incident = self.get_incident(incident_id)
        if not incident:
            return False
        
        incident.status = status
        incident.updated_at = datetime.now(timezone.utc)
        
        if assigned_to:
            incident.assigned_to = assigned_to
        
        if status == IncidentStatus.RESOLVED.value or status == IncidentStatus.CLOSED.value:
            incident.resolved_at = datetime.now(timezone.utc)
            if resolution_notes:
                incident.resolution_notes = resolution_notes
        
        self.db.commit()
        return True
    
    def assign_incident(self, incident_id: int, assigned_to: str) -> bool:
        """Assign incident to a user."""
        incident = self.get_incident(incident_id)
        if not incident:
            return False
        
        incident.assigned_to = assigned_to
        incident.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        
        return True
    
    def get_incident_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get incident statistics."""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        total_incidents = self.db.query(SecurityIncident).filter(
            SecurityIncident.created_at >= start_date
        ).count()
        
        by_status = {}
        by_severity = {}
        
        incidents = self.db.query(SecurityIncident).filter(
            SecurityIncident.created_at >= start_date
        ).all()
        
        for incident in incidents:
            # Count by status
            status = incident.status
            by_status[status] = by_status.get(status, 0) + 1
            
            # Count by severity
            severity = incident.severity
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Calculate mean time to resolution
        resolved_incidents = [i for i in incidents if i.resolved_at]
        mttr = None
        if resolved_incidents:
            total_time = sum(
                (i.resolved_at - i.created_at).total_seconds()
                for i in resolved_incidents
            )
            mttr = total_time / len(resolved_incidents) / 3600  # Convert to hours
        
        return {
            "total_incidents": total_incidents,
            "by_status": by_status,
            "by_severity": by_severity,
            "mean_time_to_resolution_hours": mttr,
            "period_days": days
        }







