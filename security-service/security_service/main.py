"""Security Service FastAPI application."""

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from .config import config
from .database import get_db, init_db
from .monitoring.ids import IntrusionDetectionSystem
from .monitoring.alerting import AlertManager
from .monitoring.anomaly import AnomalyDetectionEngine
from .protection.firewall import FirewallAutomation
from .protection.ddos import DDoSProtection
from .protection.rate_limit import RateLimiter
from .protection.access_control import AccessControlEngine
from .intelligence.ip_reputation import IPReputationService
from .intelligence.malware import MalwareScanner
from .intelligence.vulnerability import VulnerabilityScanner
from .intelligence.patch_management import PatchManager
from .siem.engine import SIEMEngine
from .siem.incidents import IncidentManager
from .compliance.audit import AuditLogger
from .compliance.reporting import ComplianceReporter
from .compliance.backup_verification import BackupVerifier
from .integration.prometheus import PrometheusMetrics
from .models.security_events import SecurityEvent
from .models.incidents import SecurityIncident
from .models.threats import ThreatIntelligence, FirewallRule, VulnerabilityScan, PatchStatus, AuditLog

import pydantic
from typing import List, Optional
from datetime import datetime, timedelta, timezone


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    init_db()
    yield
    # Shutdown


app = FastAPI(
    title="Security Service",
    description="Comprehensive security monitoring and protection framework",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection
def get_ids(db: Session = Depends(get_db)) -> IntrusionDetectionSystem:
    return IntrusionDetectionSystem(db)


def get_alert_manager(db: Session = Depends(get_db)) -> AlertManager:
    return AlertManager(db)


def get_firewall(db: Session = Depends(get_db)) -> FirewallAutomation:
    return FirewallAutomation(db)


def get_ddos_protection(db: Session = Depends(get_db)) -> DDoSProtection:
    firewall = get_firewall(db)
    return DDoSProtection(db, firewall)


def get_rate_limiter() -> RateLimiter:
    return RateLimiter()


def get_access_control(db: Session = Depends(get_db)) -> AccessControlEngine:
    return AccessControlEngine(db)


def get_ip_reputation(db: Session = Depends(get_db)) -> IPReputationService:
    return IPReputationService(db)


def get_siem(db: Session = Depends(get_db)) -> SIEMEngine:
    return SIEMEngine(db)


def get_incident_manager(db: Session = Depends(get_db)) -> IncidentManager:
    return IncidentManager(db)


def get_audit_logger(db: Session = Depends(get_db)) -> AuditLogger:
    return AuditLogger(db)


# Middleware for IDS and rate limiting
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Security middleware for IDS, rate limiting, and access control."""
    # Skip security checks for health and metrics endpoints
    if request.url.path in ["/health", "/metrics"]:
        return await call_next(request)
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Access control
        access_control = AccessControlEngine(db)
        client_ip = request.client.host if request.client else "unknown"
        allowed, reason = access_control.check_access(client_ip)
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=reason or "Access denied"
            )
        
        # Rate limiting
        rate_limiter = RateLimiter()
        allowed, remaining, reset_time = rate_limiter.check_ip_rate_limit(client_ip)
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_time)
                }
            )
        
        # DDoS protection
        firewall = FirewallAutomation(db)
        ddos_protection = DDoSProtection(db, firewall)
        ddos_event = ddos_protection.analyze_request(client_ip)
        if ddos_event:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="DDoS protection triggered"
            )
        
        # IDS analysis
        ids = IntrusionDetectionSystem(db)
        security_event = await ids.analyze_request(request)
        
        if security_event:
            # Send alert
            alert_manager = AlertManager(db)
            await alert_manager.alert_on_security_event(security_event)
            
            # Process with SIEM
            siem = SIEMEngine(db)
            incident = siem.process_event(security_event)
        
        response = await call_next(request)
        return response
    finally:
        db.close()


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "security-service"}


# Prometheus metrics
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    metrics_data = PrometheusMetrics.get_metrics()
    return Response(content=metrics_data, media_type=PrometheusMetrics.get_content_type())


# Security Events API
@app.get("/api/security/events")
async def list_security_events(
    skip: int = 0,
    limit: int = 100,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List security events."""
    query = db.query(SecurityEvent)
    
    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type)
    if severity:
        query = query.filter(SecurityEvent.severity == severity)
    
    events = query.order_by(SecurityEvent.detected_at.desc()).offset(skip).limit(limit).all()
    return {"events": events, "total": query.count()}


@app.get("/api/security/events/{event_id}")
async def get_security_event(event_id: int, db: Session = Depends(get_db)):
    """Get security event details."""
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


# Incidents API
@app.get("/api/security/incidents")
async def list_incidents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List security incidents."""
    incident_manager = get_incident_manager(db)
    
    if status:
        incidents = db.query(SecurityIncident).filter(
            SecurityIncident.status == status
        ).order_by(SecurityIncident.created_at.desc()).offset(skip).limit(limit).all()
    elif severity:
        incidents = db.query(SecurityIncident).filter(
            SecurityIncident.severity == severity
        ).order_by(SecurityIncident.created_at.desc()).offset(skip).limit(limit).all()
    else:
        incidents = incident_manager.get_active_incidents()
    
    return {"incidents": incidents, "total": len(incidents)}


@app.get("/api/security/incidents/{incident_id}")
async def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Get incident details."""
    incident_manager = get_incident_manager(db)
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Get timeline
    siem = get_siem(db)
    timeline = siem.get_incident_timeline(incident_id)
    
    return {
        "incident": incident,
        "timeline": timeline
    }


@app.post("/api/security/incidents")
async def create_incident(
    incident_type: str,
    severity: str,
    title: str,
    description: str,
    db: Session = Depends(get_db)
):
    """Create a new incident."""
    incident_manager = get_incident_manager(db)
    incident = incident_manager.create_incident(
        incident_type=incident_type,
        severity=severity,
        title=title,
        description=description
    )
    return incident


@app.put("/api/security/incidents/{incident_id}")
async def update_incident(
    incident_id: int,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    resolution_notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update incident."""
    incident_manager = get_incident_manager(db)
    success = incident_manager.update_incident_status(
        incident_id=incident_id,
        status=status or "open",
        assigned_to=assigned_to,
        resolution_notes=resolution_notes
    )
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"success": True}


# Threat Intelligence API
@app.get("/api/security/threats")
async def list_threats(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List threat intelligence entries."""
    threats = db.query(ThreatIntelligence).order_by(
        ThreatIntelligence.updated_at.desc()
    ).offset(skip).limit(limit).all()
    return {"threats": threats, "total": db.query(ThreatIntelligence).count()}


@app.get("/api/security/threats/ip/{ip_address}")
async def get_ip_reputation(ip_address: str, db: Session = Depends(get_db)):
    """Get IP reputation."""
    ip_reputation = get_ip_reputation(db)
    threat_intel = await ip_reputation.check_ip_reputation(ip_address)
    return threat_intel


# Firewall Rules API
@app.get("/api/security/firewall/rules")
async def list_firewall_rules(
    rule_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List firewall rules."""
    firewall = get_firewall(db)
    rules = firewall.get_active_rules(rule_type=rule_type)
    return {"rules": rules}


@app.post("/api/security/firewall/rules")
async def create_firewall_rule(
    rule_type: str,
    target: str,
    action: str,
    reason: str,
    duration_hours: int = 24,
    db: Session = Depends(get_db)
):
    """Create firewall rule."""
    firewall = get_firewall(db)
    if rule_type == "ip_block":
        rule = firewall.create_block_rule(target, reason, duration_hours)
    else:
        raise HTTPException(status_code=400, detail="Invalid rule type")
    return rule


@app.delete("/api/security/firewall/rules/{rule_id}")
async def delete_firewall_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete firewall rule."""
    firewall = get_firewall(db)
    success = firewall.delete_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"success": True}


# Vulnerabilities API
@app.get("/api/security/vulnerabilities")
async def list_vulnerabilities(
    resolved: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List vulnerabilities."""
    query = db.query(VulnerabilityScan)
    
    if resolved is not None:
        query = query.filter(VulnerabilityScan.resolved == resolved)
    if severity:
        query = query.filter(VulnerabilityScan.severity == severity)
    
    vulnerabilities = query.order_by(VulnerabilityScan.detected_at.desc()).all()
    return {"vulnerabilities": vulnerabilities}


@app.post("/api/security/vulnerabilities/scan")
async def trigger_vulnerability_scan(
    scan_type: str = "dependency",
    target: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Trigger vulnerability scan."""
    scanner = VulnerabilityScanner(db)
    
    if scan_type == "dependency":
        vulnerabilities = await scanner.scan_dependencies(target or "requirements.txt")
    elif scan_type == "container":
        if not target:
            raise HTTPException(status_code=400, detail="Container image name required")
        vulnerabilities = await scanner.scan_container(target)
    else:
        raise HTTPException(status_code=400, detail="Invalid scan type")
    
    return {"vulnerabilities": vulnerabilities, "count": len(vulnerabilities)}


# Audit Logs API
@app.get("/api/security/audit")
async def get_audit_logs(
    event_type: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get audit logs."""
    audit_logger = get_audit_logger(db)
    logs = audit_logger.get_audit_logs(
        event_type=event_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    return {"logs": logs}


# Compliance Reports API
@app.get("/api/security/compliance/report")
async def get_compliance_report(
    report_type: str = "security_audit",
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get compliance report."""
    reporter = ComplianceReporter(db)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    if report_type == "security_audit":
        report = reporter.generate_security_audit_report(start_date, end_date)
    elif report_type == "access_control":
        report = reporter.generate_access_control_report(start_date, end_date)
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")
    
    return report


