"""Prometheus metrics exporter."""

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any
from ..config import config


# Security event metrics
security_events_total = Counter(
    'security_events_total',
    'Total number of security events',
    ['event_type', 'severity']
)

intrusion_attempts_total = Counter(
    'intrusion_attempts_total',
    'Total number of intrusion attempts',
    ['attack_type']
)

blocked_ips_total = Gauge(
    'blocked_ips_total',
    'Total number of blocked IP addresses'
)

rate_limit_hits_total = Counter(
    'rate_limit_hits_total',
    'Total number of rate limit violations',
    ['identifier_type']
)

ddos_attacks_detected = Counter(
    'ddos_attacks_detected',
    'Total number of DDoS attacks detected'
)

vulnerability_scans_total = Counter(
    'vulnerability_scans_total',
    'Total number of vulnerability scans performed',
    ['scan_type']
)

security_alerts_active = Gauge(
    'security_alerts_active',
    'Number of active security alerts',
    ['severity']
)

firewall_rules_active = Gauge(
    'firewall_rules_active',
    'Number of active firewall rules',
    ['rule_type']
)

threat_intelligence_updates = Counter(
    'threat_intelligence_updates',
    'Total number of threat intelligence updates',
    ['source']
)

vulnerabilities_detected = Gauge(
    'vulnerabilities_detected',
    'Number of detected vulnerabilities',
    ['severity', 'resolved']
)

incidents_active = Gauge(
    'incidents_active',
    'Number of active security incidents',
    ['severity', 'status']
)

audit_log_entries_total = Counter(
    'audit_log_entries_total',
    'Total number of audit log entries',
    ['event_type']
)

# Response time histogram
security_event_processing_time = Histogram(
    'security_event_processing_seconds',
    'Time spent processing security events',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)


class PrometheusMetrics:
    """Prometheus metrics manager."""
    
    @staticmethod
    def record_security_event(event_type: str, severity: str):
        """Record a security event."""
        security_events_total.labels(
            event_type=event_type,
            severity=severity
        ).inc()
    
    @staticmethod
    def record_intrusion_attempt(attack_type: str):
        """Record an intrusion attempt."""
        intrusion_attempts_total.labels(attack_type=attack_type).inc()
    
    @staticmethod
    def update_blocked_ips(count: int):
        """Update blocked IPs count."""
        blocked_ips_total.set(count)
    
    @staticmethod
    def record_rate_limit_hit(identifier_type: str):
        """Record a rate limit violation."""
        rate_limit_hits_total.labels(identifier_type=identifier_type).inc()
    
    @staticmethod
    def record_ddos_attack():
        """Record a DDoS attack."""
        ddos_attacks_detected.inc()
    
    @staticmethod
    def record_vulnerability_scan(scan_type: str):
        """Record a vulnerability scan."""
        vulnerability_scans_total.labels(scan_type=scan_type).inc()
    
    @staticmethod
    def update_active_alerts(severity: str, count: int):
        """Update active alerts count."""
        security_alerts_active.labels(severity=severity).set(count)
    
    @staticmethod
    def update_active_firewall_rules(rule_type: str, count: int):
        """Update active firewall rules count."""
        firewall_rules_active.labels(rule_type=rule_type).set(count)
    
    @staticmethod
    def record_threat_intel_update(source: str):
        """Record threat intelligence update."""
        threat_intelligence_updates.labels(source=source).inc()
    
    @staticmethod
    def update_vulnerabilities(severity: str, resolved: str, count: int):
        """Update vulnerabilities count."""
        vulnerabilities_detected.labels(
            severity=severity,
            resolved=resolved
        ).set(count)
    
    @staticmethod
    def update_active_incidents(severity: str, status: str, count: int):
        """Update active incidents count."""
        incidents_active.labels(
            severity=severity,
            status=status
        ).set(count)
    
    @staticmethod
    def record_audit_log(event_type: str):
        """Record an audit log entry."""
        audit_log_entries_total.labels(event_type=event_type).inc()
    
    @staticmethod
    def get_metrics() -> bytes:
        """Get Prometheus metrics in text format."""
        return generate_latest()
    
    @staticmethod
    def get_content_type() -> str:
        """Get content type for metrics endpoint."""
        return CONTENT_TYPE_LATEST



