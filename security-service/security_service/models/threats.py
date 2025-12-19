"""Threat intelligence models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ThreatIntelligence(Base):
    """Threat intelligence model."""
    __tablename__ = "threat_intelligence"
    
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=False, unique=True, index=True)
    reputation_score = Column(Float, nullable=False, index=True)  # 0-100, 0 = malicious, 100 = clean
    confidence_level = Column(String(20), nullable=False)  # low, medium, high
    threat_categories = Column(JSON, nullable=True)  # List of threat categories
    is_malicious = Column(String(10), default="false", nullable=False, index=True)
    source = Column(String(100), nullable=False)  # abuseipdb, virustotal, internal, etc.
    country = Column(String(2), nullable=True)
    asn = Column(String(50), nullable=True)
    isp = Column(String(255), nullable=True)
    last_seen = Column(DateTime, nullable=True)
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    metadata = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_threat_intel_ip_reputation', 'ip_address', 'reputation_score'),
        Index('idx_threat_intel_malicious', 'is_malicious', 'reputation_score'),
    )


class FirewallRule(Base):
    """Firewall rule model."""
    __tablename__ = "firewall_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_type = Column(String(50), nullable=False)  # ip_block, port_block, rate_limit, geo_block
    target = Column(String(500), nullable=False)  # IP address, port, country code, etc.
    action = Column(String(20), nullable=False)  # block, allow, rate_limit
    reason = Column(Text, nullable=True)
    source = Column(String(100), nullable=False)  # automated, manual, threat_intel
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    is_active = Column(String(10), default="true", nullable=False, index=True)
    metadata = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_firewall_rules_active_expires', 'is_active', 'expires_at'),
        Index('idx_firewall_rules_type_target', 'rule_type', 'target'),
    )


class VulnerabilityScan(Base):
    """Vulnerability scan model."""
    __tablename__ = "vulnerability_scans"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_type = Column(String(50), nullable=False)  # dependency, container, system, application
    target = Column(String(500), nullable=False)  # Package name, image name, system identifier
    vulnerability_id = Column(String(100), nullable=False, index=True)  # CVE ID, etc.
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    cvss_score = Column(Float, nullable=True)
    fixed_version = Column(String(100), nullable=True)
    current_version = Column(String(100), nullable=True)
    package_name = Column(String(255), nullable=True, index=True)
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved = Column(String(10), default="false", nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    remediation_notes = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_vuln_scans_severity_resolved', 'severity', 'resolved'),
        Index('idx_vuln_scans_target_type', 'target', 'scan_type'),
    )


class PatchStatus(Base):
    """Patch status model."""
    __tablename__ = "patch_status"
    
    id = Column(Integer, primary_key=True, index=True)
    patch_type = Column(String(50), nullable=False)  # system, docker, python, application
    component_name = Column(String(255), nullable=False, index=True)
    current_version = Column(String(100), nullable=False)
    available_version = Column(String(100), nullable=True)
    is_security_patch = Column(String(10), default="false", nullable=False, index=True)
    patch_available = Column(String(10), default="false", nullable=False, index=True)
    last_checked = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_applied = Column(DateTime, nullable=True)
    applied_by = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)  # up_to_date, update_available, update_applied, failed
    metadata = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_patch_status_type_security', 'patch_type', 'is_security_patch'),
        Index('idx_patch_status_available', 'patch_available', 'is_security_patch'),
    )


class AuditLog(Base):
    """Audit log model."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # auth, config_change, data_access, admin_action
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String(255), nullable=True, index=True)
    action = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=True)  # user, service, config, etc.
    resource_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(String(500), nullable=True)
    success = Column(String(10), nullable=False, index=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    integrity_hash = Column(String(64), nullable=True)  # SHA-256 hash for tamper detection
    
    __table_args__ = (
        Index('idx_audit_logs_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_logs_type_timestamp', 'event_type', 'timestamp'),
        Index('idx_audit_logs_timestamp', 'timestamp'),
    )
