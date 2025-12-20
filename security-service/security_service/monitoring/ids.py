"""Intrusion Detection System."""

import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import Request
from sqlalchemy.orm import Session
from ..models.security_events import SecurityEvent, EventType, EventSeverity
from ..database import get_db


class IntrusionDetectionSystem:
    """Intrusion Detection System for analyzing requests and detecting threats."""
    
    def __init__(self, db: Session):
        self.db = db
        self.signatures = self._load_signatures()
        self.brute_force_threshold = 5
        self.brute_force_window = timedelta(seconds=300)
        
    def _load_signatures(self) -> Dict[str, List[str]]:
        """Load detection signatures."""
        return {
            "sql_injection": [
                r"(\bUNION\b.*\bSELECT\b)",
                r"(\bOR\b.*=.*)",
                r"(\bAND\b.*=.*)",
                r"('.*OR.*'.*=.*')",
                r"(\bSELECT\b.*\bFROM\b)",
                r"(\bINSERT\b.*\bINTO\b)",
                r"(\bDELETE\b.*\bFROM\b)",
                r"(\bDROP\b.*\bTABLE\b)",
                r"(\bEXEC\b.*\()",
                r"(\bEXECUTE\b.*\()",
            ],
            "xss": [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"onerror\s*=",
                r"onload\s*=",
                r"onclick\s*=",
                r"<iframe[^>]*>",
                r"<img[^>]*onerror",
            ],
            "path_traversal": [
                r"\.\./",
                r"\.\.\\",
                r"\.\.%2F",
                r"\.\.%5C",
                r"/etc/passwd",
                r"/etc/shadow",
                r"\\windows\\system32",
            ],
            "command_injection": [
                r"[;&|`]\s*(ls|cat|pwd|whoami|id|uname)",
                r"\|\s*(nc|netcat|wget|curl)",
                r"`.*`",
                r"\$\(.*\)",
            ],
        }
    
    async def analyze_request(self, request: Request, user_id: Optional[int] = None, 
                             username: Optional[str] = None) -> Optional[SecurityEvent]:
        """Analyze a request for intrusion patterns."""
        if not self.db:
            return None
            
        # Get request details
        source_ip = self._get_client_ip(request)
        path = str(request.url.path)
        method = request.method
        user_agent = request.headers.get("user-agent", "")
        query_params = str(request.url.query)
        
        # Check for signature-based attacks
        event = await self._check_signatures(source_ip, path, query_params, method, 
                                            user_agent, user_id, username)
        if event:
            return event
        
        # Check for brute force attempts
        event = await self._check_brute_force(source_ip, user_id, username)
        if event:
            return event
        
        # Check for unusual patterns
        event = await self._check_unusual_patterns(source_ip, path, method, user_id, username)
        if event:
            return event
        
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded IP
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def _check_signatures(self, source_ip: str, path: str, query_params: str,
                               method: str, user_agent: str, user_id: Optional[int],
                               username: Optional[str]) -> Optional[SecurityEvent]:
        """Check request against attack signatures."""
        combined = f"{path} {query_params}".lower()
        
        for attack_type, patterns in self.signatures.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    return self._create_event(
                        event_type=self._map_attack_type(attack_type),
                        severity=EventSeverity.HIGH,
                        source_ip=source_ip,
                        user_id=user_id,
                        username=username,
                        endpoint=path,
                        method=method,
                        user_agent=user_agent,
                        description=f"Detected {attack_type} attempt in request",
                        raw_data={
                            "path": path,
                            "query": query_params,
                            "pattern": pattern,
                            "attack_type": attack_type
                        }
                    )
        
        return None
    
    def _map_attack_type(self, attack_type: str) -> EventType:
        """Map attack type to event type."""
        mapping = {
            "sql_injection": EventType.SQL_INJECTION,
            "xss": EventType.XSS_ATTEMPT,
            "path_traversal": EventType.PATH_TRAVERSAL,
            "command_injection": EventType.INTRUSION_ATTEMPT,
        }
        return mapping.get(attack_type, EventType.INTRUSION_ATTEMPT)
    
    async def _check_brute_force(self, source_ip: str, user_id: Optional[int],
                                 username: Optional[str]) -> Optional[SecurityEvent]:
        """Check for brute force login attempts."""
        # Count failed login attempts in the time window
        window_start = datetime.now(timezone.utc) - self.brute_force_window
        
        failed_attempts = self.db.query(SecurityEvent).filter(
            SecurityEvent.source_ip == source_ip,
            SecurityEvent.event_type == EventType.UNAUTHORIZED_ACCESS,
            SecurityEvent.detected_at >= window_start
        ).count()
        
        if failed_attempts >= self.brute_force_threshold:
            return self._create_event(
                event_type=EventType.BRUTE_FORCE,
                severity=EventSeverity.HIGH,
                source_ip=source_ip,
                user_id=user_id,
                username=username,
                description=f"Brute force attack detected: {failed_attempts} failed attempts from {source_ip}",
                metadata={"failed_attempts": failed_attempts}
            )
        
        return None
    
    async def _check_unusual_patterns(self, source_ip: str, path: str, method: str,
                                    user_id: Optional[int], username: Optional[str]) -> Optional[SecurityEvent]:
        """Check for unusual access patterns."""
        # Check for port scanning patterns (multiple endpoints in short time)
        window_start = datetime.now(timezone.utc) - timedelta(seconds=60)
        
        recent_requests = self.db.query(SecurityEvent).filter(
            SecurityEvent.source_ip == source_ip,
            SecurityEvent.detected_at >= window_start
        ).count()
        
        if recent_requests > 50:  # Threshold for port scanning
            return self._create_event(
                event_type=EventType.PORT_SCAN,
                severity=EventSeverity.MEDIUM,
                source_ip=source_ip,
                user_id=user_id,
                username=username,
                endpoint=path,
                method=method,
                description=f"Possible port scanning detected: {recent_requests} requests in 60 seconds",
                metadata={"request_count": recent_requests}
            )
        
        return None
    
    def _create_event(self, event_type: EventType, severity: EventSeverity,
                     source_ip: str, description: str, user_id: Optional[int] = None,
                     username: Optional[str] = None, endpoint: Optional[str] = None,
                     method: Optional[str] = None, user_agent: Optional[str] = None,
                     raw_data: Optional[Dict[str, Any]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> SecurityEvent:
        """Create a security event."""
        event = SecurityEvent(
            event_type=event_type.value,
            severity=severity.value,
            source_ip=source_ip,
            user_id=user_id,
            username=username,
            endpoint=endpoint,
            method=method,
            user_agent=user_agent,
            description=description,
            raw_data=raw_data,
            metadata=metadata,
            detected_at=datetime.now(timezone.utc)
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        return event
    
    def record_failed_login(self, source_ip: str, username: Optional[str] = None):
        """Record a failed login attempt."""
        self._create_event(
            event_type=EventType.UNAUTHORIZED_ACCESS,
            severity=EventSeverity.MEDIUM,
            source_ip=source_ip,
            username=username,
            description=f"Failed login attempt from {source_ip}",
            metadata={"action": "failed_login"}
        )


