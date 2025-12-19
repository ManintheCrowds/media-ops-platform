"""Log aggregation service."""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_


class LogAggregator:
    """Centralized log aggregation service."""
    
    def __init__(self, db: Session, log_dir: str = "/var/log/security-service"):
        self.db = db
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def collect_application_log(self, service_name: str, level: str, message: str,
                               metadata: Optional[Dict[str, Any]] = None):
        """Collect application log from a service."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": service_name,
            "level": level,
            "message": message,
            "metadata": metadata or {}
        }
        
        # Write to file
        log_file = self.log_dir / f"{service_name}.log"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Store in database if critical
        if level in ["ERROR", "CRITICAL"]:
            self._store_log_entry(log_entry)
    
    def collect_access_log(self, source_ip: str, method: str, path: str,
                          status_code: int, response_time: float,
                          user_agent: Optional[str] = None,
                          user_id: Optional[int] = None):
        """Collect access log entry."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "access",
            "source_ip": source_ip,
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time": response_time,
            "user_agent": user_agent,
            "user_id": user_id
        }
        
        # Write to file
        log_file = self.log_dir / "access.log"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def collect_security_event(self, event_type: str, severity: str,
                              source_ip: str, description: str,
                              metadata: Optional[Dict[str, Any]] = None):
        """Collect security event log."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "security_event",
            "event_type": event_type,
            "severity": severity,
            "source_ip": source_ip,
            "description": description,
            "metadata": metadata or {}
        }
        
        # Write to file
        log_file = self.log_dir / "security.log"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def _store_log_entry(self, log_entry: Dict[str, Any]):
        """Store critical log entry in database."""
        # This would integrate with a log storage table if needed
        # For now, we rely on file-based storage
        pass
    
    def search_logs(self, service_name: Optional[str] = None,
                   level: Optional[str] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """Search aggregated logs."""
        results = []
        
        # Search file-based logs
        if service_name:
            log_file = self.log_dir / f"{service_name}.log"
        else:
            log_file = self.log_dir / "access.log"
        
        if not log_file.exists():
            return results
        
        # Read and filter logs
        with open(log_file, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    
                    # Apply filters
                    if start_time and entry_time < start_time:
                        continue
                    if end_time and entry_time > end_time:
                        continue
                    if level and entry.get("level") != level:
                        continue
                    
                    results.append(entry)
                    
                    if len(results) >= limit:
                        break
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return results
    
    def get_log_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get log statistics for the specified time period."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        stats = {
            "total_logs": 0,
            "by_level": {},
            "by_service": {},
            "error_count": 0,
            "warning_count": 0
        }
        
        # Scan all log files
        for log_file in self.log_dir.glob("*.log"):
            with open(log_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        
                        if entry_time < start_time or entry_time > end_time:
                            continue
                        
                        stats["total_logs"] += 1
                        
                        # Count by level
                        level = entry.get("level", "INFO")
                        stats["by_level"][level] = stats["by_level"].get(level, 0) + 1
                        
                        if level == "ERROR":
                            stats["error_count"] += 1
                        elif level == "WARNING":
                            stats["warning_count"] += 1
                        
                        # Count by service
                        service = entry.get("service", "unknown")
                        stats["by_service"][service] = stats["by_service"].get(service, 0) + 1
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return stats
    
    def cleanup_old_logs(self, retention_days: int = 90):
        """Clean up logs older than retention period."""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        for log_file in self.log_dir.glob("*.log"):
            # For file-based logs, we could implement rotation
            # For now, we'll keep all logs and let the system handle rotation
            pass

