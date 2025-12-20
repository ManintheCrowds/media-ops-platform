"""DDoS protection service."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from ..models.security_events import SecurityEvent, EventType, EventSeverity
from ..config import config
from .firewall import FirewallAutomation


class DDoSProtection:
    """DDoS detection and mitigation."""
    
    def __init__(self, db: Session, firewall: FirewallAutomation):
        self.db = db
        self.firewall = firewall
        self.threshold_requests = config.ddos_threshold_requests
        self.threshold_window = timedelta(seconds=config.ddos_threshold_window)
        self.block_duration = config.ddos_block_duration
        self.request_counts = defaultdict(list)  # In-memory tracking (use Redis in production)
        
    def analyze_request(self, source_ip: str) -> Optional[SecurityEvent]:
        """Analyze request for DDoS patterns."""
        now = datetime.now(timezone.utc)
        window_start = now - self.threshold_window
        
        # Track request
        self.request_counts[source_ip].append(now)
        
        # Clean old requests outside window
        self.request_counts[source_ip] = [
            req_time for req_time in self.request_counts[source_ip]
            if req_time >= window_start
        ]
        
        # Check threshold
        request_count = len(self.request_counts[source_ip])
        
        if request_count >= self.threshold_requests:
            # DDoS detected
            return self._create_ddos_event(source_ip, request_count)
        
        return None
    
    def _create_ddos_event(self, source_ip: str, request_count: int) -> SecurityEvent:
        """Create DDoS security event."""
        event = SecurityEvent(
            event_type=EventType.DDoS_ATTACK.value,
            severity=EventSeverity.CRITICAL.value,
            source_ip=source_ip,
            description=f"DDoS attack detected: {request_count} requests in {self.threshold_window.total_seconds()} seconds",
            detected_at=datetime.now(timezone.utc),
            metadata={
                "request_count": request_count,
                "threshold": self.threshold_requests,
                "window_seconds": self.threshold_window.total_seconds()
            }
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        # Automatically block the IP
        self.firewall.create_block_rule(
            ip_address=source_ip,
            reason=f"DDoS attack: {request_count} requests",
            duration_hours=self.block_duration // 3600,
            source="ddos_protection"
        )
        
        return event
    
    def get_ddos_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get DDoS protection statistics."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        ddos_events = self.db.query(SecurityEvent).filter(
            SecurityEvent.event_type == EventType.DDoS_ATTACK.value,
            SecurityEvent.detected_at >= start_time,
            SecurityEvent.detected_at <= end_time
        ).all()
        
        blocked_ips = set()
        total_attacks = len(ddos_events)
        
        for event in ddos_events:
            if event.source_ip:
                blocked_ips.add(event.source_ip)
        
        return {
            "total_attacks": total_attacks,
            "unique_attacking_ips": len(blocked_ips),
            "blocked_ips": list(blocked_ips),
            "time_period_hours": hours
        }
    
    def cleanup_old_tracking(self):
        """Clean up old request tracking data."""
        cutoff = datetime.now(timezone.utc) - self.threshold_window
        
        for ip in list(self.request_counts.keys()):
            self.request_counts[ip] = [
                req_time for req_time in self.request_counts[ip]
                if req_time >= cutoff
            ]
            
            # Remove empty entries
            if not self.request_counts[ip]:
                del self.request_counts[ip]


