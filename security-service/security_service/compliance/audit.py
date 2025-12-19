"""Audit logging service."""

import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.threats import AuditLog


class AuditLogger:
    """Comprehensive audit logging with integrity verification."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def log_event(self, event_type: str, action: str, user_id: Optional[int] = None,
                  username: Optional[str] = None, resource_type: Optional[str] = None,
                  resource_id: Optional[str] = None, ip_address: Optional[str] = None,
                  user_agent: Optional[str] = None, success: bool = True,
                  details: Optional[Dict[str, Any]] = None) -> AuditLog:
        """Log an audit event."""
        # Calculate integrity hash
        log_data = {
            "event_type": event_type,
            "action": action,
            "user_id": user_id,
            "username": username,
            "timestamp": datetime.utcnow().isoformat()
        }
        integrity_hash = self._calculate_hash(log_data)
        
        audit_entry = AuditLog(
            event_type=event_type,
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success="true" if success else "false",
            details=details or {},
            timestamp=datetime.utcnow(),
            integrity_hash=integrity_hash
        )
        
        self.db.add(audit_entry)
        self.db.commit()
        self.db.refresh(audit_entry)
        
        return audit_entry
    
    def _calculate_hash(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash for integrity verification."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def verify_integrity(self, audit_entry: AuditLog) -> bool:
        """Verify integrity of audit log entry."""
        log_data = {
            "event_type": audit_entry.event_type,
            "action": audit_entry.action,
            "user_id": audit_entry.user_id,
            "username": audit_entry.username,
            "timestamp": audit_entry.timestamp.isoformat()
        }
        expected_hash = self._calculate_hash(log_data)
        return audit_entry.integrity_hash == expected_hash
    
    def get_audit_logs(self, event_type: Optional[str] = None,
                      user_id: Optional[int] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      limit: int = 100) -> list[AuditLog]:
        """Get audit logs with filters."""
        query = self.db.query(AuditLog)
        
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    def detect_tampering(self, start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> list[AuditLog]:
        """Detect tampered audit log entries."""
        query = self.db.query(AuditLog)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        entries = query.all()
        tampered = []
        
        for entry in entries:
            if not self.verify_integrity(entry):
                tampered.append(entry)
        
        return tampered

