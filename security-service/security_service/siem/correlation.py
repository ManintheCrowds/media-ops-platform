"""Correlation rules engine."""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from ..models.security_events import SecurityEvent, EventType
from ..models.incidents import SecurityIncident, IncidentType, IncidentSeverity, IncidentStatus


class CorrelationRule:
    """Correlation rule definition."""
    
    def __init__(self, rule_id: str, name: str, description: str, enabled: bool = True):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.enabled = enabled
        self.time_window = timedelta(minutes=5)
        self.event_types: List[str] = []
        self.threshold: int = 1
        self.incident_type: IncidentType = IncidentType.OTHER
        self.incident_severity: IncidentSeverity = IncidentSeverity.MEDIUM


class CorrelationEngine:
    """Event correlation engine."""
    
    def __init__(self, db: Session):
        self.db = db
        self.rules = self._load_default_rules()
        
    def _load_default_rules(self) -> List[CorrelationRule]:
        """Load default correlation rules."""
        rules = []
        
        # Brute force rule: Multiple failed logins
        brute_force_rule = CorrelationRule(
            rule_id="brute_force",
            name="Brute Force Attack",
            description="Multiple failed login attempts from same IP",
            enabled=True
        )
        brute_force_rule.event_types = [EventType.UNAUTHORIZED_ACCESS.value]
        brute_force_rule.threshold = 5
        brute_force_rule.time_window = timedelta(minutes=5)
        brute_force_rule.incident_type = IncidentType.INTRUSION_ATTEMPT
        brute_force_rule.incident_severity = IncidentSeverity.HIGH
        rules.append(brute_force_rule)
        
        # Coordinated attack rule: DDoS + Intrusion
        coordinated_rule = CorrelationRule(
            rule_id="coordinated_attack",
            name="Coordinated Attack",
            description="DDoS attack combined with intrusion attempts",
            enabled=True
        )
        coordinated_rule.event_types = [
            EventType.DDoS_ATTACK.value,
            EventType.INTRUSION_ATTEMPT.value
        ]
        coordinated_rule.threshold = 2
        coordinated_rule.time_window = timedelta(minutes=10)
        coordinated_rule.incident_type = IncidentType.INTRUSION_ATTEMPT
        coordinated_rule.incident_severity = IncidentSeverity.CRITICAL
        rules.append(coordinated_rule)
        
        # Multiple attack types rule
        multi_attack_rule = CorrelationRule(
            rule_id="multiple_attack_types",
            name="Multiple Attack Vectors",
            description="Multiple different attack types from same source",
            enabled=True
        )
        multi_attack_rule.event_types = [
            EventType.SQL_INJECTION.value,
            EventType.XSS_ATTEMPT.value,
            EventType.PATH_TRAVERSAL.value
        ]
        multi_attack_rule.threshold = 2
        multi_attack_rule.time_window = timedelta(minutes=15)
        multi_attack_rule.incident_type = IncidentType.INTRUSION_ATTEMPT
        multi_attack_rule.incident_severity = IncidentSeverity.HIGH
        rules.append(multi_attack_rule)
        
        return rules
    
    def check_correlation(self, event: SecurityEvent) -> Optional[SecurityIncident]:
        """Check if event correlates with others to create incident."""
        if not event.source_ip:
            return None
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            if event.event_type not in rule.event_types:
                continue
            
            # Check for correlated events
            correlated_events = self._find_correlated_events(event, rule)
            
            if len(correlated_events) >= rule.threshold:
                return self._create_correlated_incident(event, correlated_events, rule)
        
        return None
    
    def _find_correlated_events(self, event: SecurityEvent, rule: CorrelationRule) -> List[SecurityEvent]:
        """Find events that correlate with the given event."""
        window_start = event.detected_at - rule.time_window
        window_end = event.detected_at + rule.time_window
        
        query = self.db.query(SecurityEvent).filter(
            SecurityEvent.detected_at >= window_start,
            SecurityEvent.detected_at <= window_end,
            SecurityEvent.event_type.in_(rule.event_types)
        )
        
        # If rule requires same source IP
        if event.source_ip:
            query = query.filter(SecurityEvent.source_ip == event.source_ip)
        
        # Exclude the current event
        query = query.filter(SecurityEvent.id != event.id)
        
        return query.all()
    
    def _create_correlated_incident(self, event: SecurityEvent, correlated_events: List[SecurityEvent],
                                   rule: CorrelationRule) -> SecurityIncident:
        """Create incident from correlated events."""
        # Check if incident already exists
        existing = self.db.query(SecurityIncident).filter(
            SecurityIncident.status.in_([
                IncidentStatus.OPEN.value,
                IncidentStatus.INVESTIGATING.value,
                IncidentStatus.CONTAINED.value
            ]),
            SecurityIncident.incident_type == rule.incident_type.value
        ).first()
        
        if existing:
            # Add event to existing incident
            event_ids = existing.related_event_ids or []
            event_ids.append(event.id)
            for e in correlated_events:
                if e.id not in event_ids:
                    event_ids.append(e.id)
            existing.related_event_ids = event_ids
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return existing
        
        # Create new incident
        all_events = [event] + correlated_events
        source_ips = list(set([e.source_ip for e in all_events if e.source_ip]))
        event_ids = [e.id for e in all_events]
        
        incident = SecurityIncident(
            incident_type=rule.incident_type.value,
            severity=rule.incident_severity.value,
            status=IncidentStatus.OPEN.value,
            title=f"{rule.name}: {len(all_events)} correlated events",
            description=rule.description,
            source_ips=source_ips,
            related_event_ids=event_ids,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            metadata={
                "rule_id": rule.rule_id,
                "correlation_count": len(all_events)
            }
        )
        
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        
        return incident







