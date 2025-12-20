"""Security event models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class EventType(str, Enum):
    """Security event types."""
    INTRUSION_ATTEMPT = "intrusion_attempt"
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS_ATTEMPT = "xss_attempt"
    PATH_TRAVERSAL = "path_traversal"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PORT_SCAN = "port_scan"
    DDoS_ATTACK = "ddos_attack"
    MALWARE_DETECTED = "malware_detected"
    VULNERABILITY_EXPLOIT = "vulnerability_exploit"
    POLICY_VIOLATION = "policy_violation"
    ANOMALY_DETECTED = "anomaly_detected"
    OTHER = "other"


class EventSeverity(str, Enum):
    """Event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEvent(Base):
    """Security event model."""
    __tablename__ = "security_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    source_ip = Column(String(45), nullable=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String(255), nullable=True)
    endpoint = Column(String(500), nullable=True)
    method = Column(String(10), nullable=True)
    user_agent = Column(String(500), nullable=True)
    description = Column(Text, nullable=False)
    raw_data = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    resolved = Column(String(10), default="false", nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('idx_security_events_source_ip_detected', 'source_ip', 'detected_at'),
        Index('idx_security_events_type_severity', 'event_type', 'severity'),
    )


