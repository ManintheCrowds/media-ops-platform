"""Security incident models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from ..base import Base


class IncidentStatus(str, Enum):
    """Incident status."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentSeverity(str, Enum):
    """Incident severity."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentType(str, Enum):
    """Incident types."""
    INTRUSION_ATTEMPT = "intrusion_attempt"
    DATA_BREACH = "data_breach"
    DDOS_ATTACK = "ddos_attack"
    MALWARE_DETECTION = "malware_detection"
    VULNERABILITY_EXPLOITATION = "vulnerability_exploitation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    POLICY_VIOLATION = "policy_violation"
    OTHER = "other"


class SecurityIncident(Base):
    """Security incident model."""
    __tablename__ = "security_incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    status = Column(String(20), default=IncidentStatus.OPEN, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    source_ips = Column(JSON, nullable=True)  # List of IPs
    affected_resources = Column(JSON, nullable=True)  # List of affected resources
    related_event_ids = Column(JSON, nullable=True)  # List of related security event IDs
    incident_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    assigned_to = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_incidents_status_severity', 'status', 'severity'),
        Index('idx_incidents_created_at', 'created_at'),
    )




