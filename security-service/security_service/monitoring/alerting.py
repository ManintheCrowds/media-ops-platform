"""Alerting system with multi-channel support."""

import smtplib
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..config import config
from ..models.security_events import SecurityEvent, EventSeverity


class AlertSeverity:
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertManager:
    """Multi-channel alerting system."""
    
    def __init__(self, db: Session):
        self.db = db
        self.sent_alerts = {}  # In-memory deduplication (use Redis in production)
        self.deduplication_window = timedelta(minutes=5)
        
    async def send_alert(self, severity: str, title: str, description: str,
                        metadata: Optional[Dict[str, Any]] = None,
                        event_id: Optional[int] = None):
        """Send alert through configured channels."""
        # Check for deduplication
        alert_key = self._generate_alert_key(severity, title, description)
        if self._is_duplicate(alert_key):
            return
        
        # Mark as sent
        self.sent_alerts[alert_key] = datetime.now(timezone.utc)
        
        # Send through all enabled channels
        if config.alert_email_enabled:
            await self._send_email_alert(severity, title, description, metadata)
        
        if config.alert_slack_webhook:
            await self._send_slack_alert(severity, title, description, metadata)
        
        if config.alert_webhook_url:
            await self._send_webhook_alert(severity, title, description, metadata, event_id)
    
    def _generate_alert_key(self, severity: str, title: str, description: str) -> str:
        """Generate deduplication key for alert."""
        content = f"{severity}:{title}:{description}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_duplicate(self, alert_key: str) -> bool:
        """Check if alert is duplicate."""
        if alert_key not in self.sent_alerts:
            return False
        
        sent_time = self.sent_alerts[alert_key]
        if datetime.now(timezone.utc) - sent_time > self.deduplication_window:
            # Expired, remove from cache
            del self.sent_alerts[alert_key]
            return False
        
        return True
    
    async def _send_email_alert(self, severity: str, title: str, description: str,
                               metadata: Optional[Dict[str, Any]] = None):
        """Send email alert."""
        if not config.alert_email_from or not config.alert_email_to:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = config.alert_email_from
            msg['To'] = ", ".join(config.alert_email_to)
            msg['Subject'] = f"[{severity.upper()}] {title}"
            
            body = f"""
Security Alert

Severity: {severity.upper()}
Title: {title}
Description: {description}

Timestamp: {datetime.now(timezone.utc).isoformat()}
"""
            if metadata:
                body += f"\nMetadata:\n{json.dumps(metadata, indent=2)}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(config.alert_email_smtp_host, config.alert_email_smtp_port) as server:
                if config.alert_email_smtp_user:
                    server.starttls()
                    server.login(config.alert_email_smtp_user, config.alert_email_smtp_password)
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    async def _send_slack_alert(self, severity: str, title: str, description: str,
                              metadata: Optional[Dict[str, Any]] = None):
        """Send Slack alert via webhook."""
        if not config.alert_slack_webhook:
            return
        
        # Map severity to color
        color_map = {
            "low": "#36a64f",      # Green
            "medium": "#ffa500",   # Orange
            "high": "#ff0000",     # Red
            "critical": "#8b0000"  # Dark red
        }
        
        payload = {
            "attachments": [{
                "color": color_map.get(severity, "#808080"),
                "title": title,
                "text": description,
                "fields": [
                    {
                        "title": "Severity",
                        "value": severity.upper(),
                        "short": True
                    },
                    {
                        "title": "Timestamp",
                        "value": datetime.now(timezone.utc).isoformat(),
                        "short": True
                    }
                ],
                "footer": "Security Monitoring System",
                "ts": int(datetime.now(timezone.utc).timestamp())
            }]
        }
        
        if metadata:
            payload["attachments"][0]["fields"].append({
                "title": "Details",
                "value": json.dumps(metadata, indent=2),
                "short": False
            })
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(config.alert_slack_webhook, json=payload, timeout=10.0)
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
    
    async def _send_webhook_alert(self, severity: str, title: str, description: str,
                                 metadata: Optional[Dict[str, Any]] = None,
                                 event_id: Optional[int] = None):
        """Send webhook alert."""
        if not config.alert_webhook_url:
            return
        
        payload = {
            "severity": severity,
            "title": title,
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": event_id,
            "metadata": metadata or {}
        }
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(config.alert_webhook_url, json=payload, timeout=10.0)
        except Exception as e:
            print(f"Failed to send webhook alert: {e}")
    
    async def alert_on_security_event(self, event: SecurityEvent):
        """Send alert for security event based on severity."""
        severity_map = {
            EventSeverity.LOW: AlertSeverity.LOW,
            EventSeverity.MEDIUM: AlertSeverity.MEDIUM,
            EventSeverity.HIGH: AlertSeverity.HIGH,
            EventSeverity.CRITICAL: AlertSeverity.CRITICAL,
        }
        
        alert_severity = severity_map.get(event.severity, AlertSeverity.MEDIUM)
        
        # Only alert on medium and above
        if alert_severity in [AlertSeverity.LOW]:
            return
        
        title = f"Security Event: {event.event_type}"
        description = event.description
        
        metadata = {
            "event_id": event.id,
            "source_ip": event.source_ip,
            "endpoint": event.endpoint,
            "method": event.method,
            "user_id": event.user_id,
            "username": event.username
        }
        
        await self.send_alert(
            severity=alert_severity,
            title=title,
            description=description,
            metadata=metadata,
            event_id=event.id
        )
    
    async def alert_on_anomaly(self, anomaly: Dict[str, Any]):
        """Send alert for detected anomaly."""
        severity = anomaly.get("severity", "medium")
        anomaly_type = anomaly.get("type", "unknown")
        description = anomaly.get("description", "Anomaly detected")
        
        await self.send_alert(
            severity=severity,
            title=f"Anomaly Detected: {anomaly_type}",
            description=description,
            metadata=anomaly
        )
    
    def cleanup_old_alerts(self):
        """Clean up old alert deduplication cache."""
        cutoff = datetime.now(timezone.utc) - self.deduplication_window
        keys_to_remove = [
            key for key, timestamp in self.sent_alerts.items()
            if timestamp < cutoff
        ]
        for key in keys_to_remove:
            del self.sent_alerts[key]



