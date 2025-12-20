"""SIEM engine for event correlation and analysis."""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..models.security_events import SecurityEvent, EventType
from ..models.incidents import SecurityIncident, IncidentType, IncidentSeverity, IncidentStatus
from .correlation import CorrelationEngine


class SIEMEngine:
    """SIEM engine for event correlation and incident generation."""
    
    def __init__(self, db: Session):
        self.db = db
        self.correlation_engine = CorrelationEngine(db)
        
    def process_event(self, event: SecurityEvent) -> Optional[SecurityIncident]:
        """Process security event and check for incident generation."""
        # Check correlation rules
        correlated_incident = self.correlation_engine.check_correlation(event)
        
        if correlated_incident:
            return correlated_incident
        
        # Check if event itself warrants an incident
        if self._should_create_incident(event):
            return self._create_incident_from_event(event)
        
        return None
    
    def _should_create_incident(self, event: SecurityEvent) -> bool:
        """Determine if event should create an incident."""
        # Critical and high severity events always create incidents
        if event.severity in ["critical", "high"]:
            return True
        
        # Certain event types always create incidents
        critical_types = [
            EventType.DDoS_ATTACK.value,
            EventType.DATA_BREACH.value if hasattr(EventType, 'DATA_BREACH') else None,
            EventType.MALWARE_DETECTED.value
        ]
        
        if event.event_type in critical_types:
            return True
        
        return False
    
    def _create_incident_from_event(self, event: SecurityEvent) -> SecurityIncident:
        """Create incident from security event."""
        incident_type = self._map_event_to_incident_type(event.event_type)
        severity = self._map_severity_to_incident_severity(event.severity)
        
        incident = SecurityIncident(
            incident_type=incident_type.value,
            severity=severity.value,
            status=IncidentStatus.OPEN.value,
            title=f"Security Incident: {event.event_type}",
            description=event.description,
            source_ips=[event.source_ip] if event.source_ip else [],
            related_event_ids=[event.id],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        
        return incident
    
    def _map_event_to_incident_type(self, event_type: str) -> IncidentType:
        """Map event type to incident type."""
        mapping = {
            EventType.INTRUSION_ATTEMPT.value: IncidentType.INTRUSION_ATTEMPT,
            EventType.DDoS_ATTACK.value: IncidentType.DDOS_ATTACK,
            EventType.MALWARE_DETECTED.value: IncidentType.MALWARE_DETECTION,
            EventType.VULNERABILITY_EXPLOIT.value: IncidentType.VULNERABILITY_EXPLOITATION,
            EventType.UNAUTHORIZED_ACCESS.value: IncidentType.UNAUTHORIZED_ACCESS,
        }
        return mapping.get(event_type, IncidentType.OTHER)
    
    def _map_severity_to_incident_severity(self, severity: str) -> IncidentSeverity:
        """Map event severity to incident severity."""
        mapping = {
            "low": IncidentSeverity.LOW,
            "medium": IncidentSeverity.MEDIUM,
            "high": IncidentSeverity.HIGH,
            "critical": IncidentSeverity.CRITICAL,
        }
        return mapping.get(severity, IncidentSeverity.MEDIUM)
    
    def get_incident_timeline(self, incident_id: int) -> List[Dict[str, Any]]:
        """Get timeline of events for an incident."""
        incident = self.db.query(SecurityIncident).filter(
            SecurityIncident.id == incident_id
        ).first()
        
        if not incident:
            return []
        
        event_ids = incident.related_event_ids or []
        if not event_ids:
            return []
        
        events = self.db.query(SecurityEvent).filter(
            SecurityEvent.id.in_(event_ids)
        ).order_by(SecurityEvent.detected_at).all()
        
        timeline = []
        for event in events:
            timeline.append({
                "timestamp": event.detected_at.isoformat(),
                "event_type": event.event_type,
                "severity": event.severity,
                "description": event.description,
                "source_ip": event.source_ip
            })
        
        return timeline



