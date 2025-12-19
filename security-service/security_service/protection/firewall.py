"""Firewall automation service."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models.threats import FirewallRule
from ..config import config


class FirewallAutomation:
    """Automated firewall rule management."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def create_block_rule(self, ip_address: str, reason: str, duration_hours: int = 24,
                          source: str = "automated") -> FirewallRule:
        """Create an IP block rule."""
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        
        rule = FirewallRule(
            rule_type="ip_block",
            target=ip_address,
            action="block",
            reason=reason,
            source=source,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            is_active="true"
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        # Apply rule to actual firewall (pfSense, iptables, etc.)
        self._apply_firewall_rule(rule)
        
        return rule
    
    def create_rate_limit_rule(self, ip_address: str, max_requests: int,
                             window_seconds: int, reason: str) -> FirewallRule:
        """Create a rate limit rule."""
        rule = FirewallRule(
            rule_type="rate_limit",
            target=ip_address,
            action="rate_limit",
            reason=reason,
            source="automated",
            created_at=datetime.utcnow(),
            is_active="true",
            metadata={
                "max_requests": max_requests,
                "window_seconds": window_seconds
            }
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        return rule
    
    def block_ip_from_threat(self, ip_address: str, threat_type: str,
                            severity: str) -> Optional[FirewallRule]:
        """Automatically block IP based on threat intelligence."""
        # Check if already blocked
        existing = self.db.query(FirewallRule).filter(
            FirewallRule.target == ip_address,
            FirewallRule.rule_type == "ip_block",
            FirewallRule.is_active == "true"
        ).first()
        
        if existing:
            return existing
        
        # Determine block duration based on severity
        duration_map = {
            "low": 1,
            "medium": 6,
            "high": 24,
            "critical": 168  # 7 days
        }
        
        duration = duration_map.get(severity, 24)
        reason = f"Automated block due to {threat_type} threat (severity: {severity})"
        
        return self.create_block_rule(ip_address, reason, duration, source="threat_intel")
    
    def get_active_rules(self, rule_type: Optional[str] = None) -> List[FirewallRule]:
        """Get all active firewall rules."""
        query = self.db.query(FirewallRule).filter(
            FirewallRule.is_active == "true"
        )
        
        if rule_type:
            query = query.filter(FirewallRule.rule_type == rule_type)
        
        # Filter out expired rules
        now = datetime.utcnow()
        rules = query.filter(
            (FirewallRule.expires_at.is_(None)) | (FirewallRule.expires_at > now)
        ).all()
        
        return rules
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if an IP address is blocked."""
        now = datetime.utcnow()
        
        rule = self.db.query(FirewallRule).filter(
            FirewallRule.target == ip_address,
            FirewallRule.rule_type == "ip_block",
            FirewallRule.action == "block",
            FirewallRule.is_active == "true",
            (FirewallRule.expires_at.is_(None)) | (FirewallRule.expires_at > now)
        ).first()
        
        return rule is not None
    
    def delete_rule(self, rule_id: int) -> bool:
        """Delete a firewall rule."""
        rule = self.db.query(FirewallRule).filter(FirewallRule.id == rule_id).first()
        if not rule:
            return False
        
        rule.is_active = "false"
        self.db.commit()
        
        # Remove from actual firewall
        self._remove_firewall_rule(rule)
        
        return True
    
    def cleanup_expired_rules(self):
        """Clean up expired firewall rules."""
        now = datetime.utcnow()
        
        expired_rules = self.db.query(FirewallRule).filter(
            FirewallRule.is_active == "true",
            FirewallRule.expires_at.isnot(None),
            FirewallRule.expires_at <= now
        ).all()
        
        for rule in expired_rules:
            rule.is_active = "false"
            self._remove_firewall_rule(rule)
        
        self.db.commit()
    
    def _apply_firewall_rule(self, rule: FirewallRule):
        """Apply rule to actual firewall system."""
        # This would integrate with:
        # - pfSense API (when configured)
        # - iptables (Linux)
        # - Docker network policies
        # - Cloud firewall APIs
        
        if config.pfsense_url and config.pfsense_api_key:
            # Apply via pfSense API
            self._apply_pfsense_rule(rule)
        else:
            # Apply via iptables or other method
            self._apply_iptables_rule(rule)
    
    def _apply_pfsense_rule(self, rule: FirewallRule):
        """Apply rule via pfSense API."""
        # This will be implemented when pfSense integration is configured
        # For now, just log
        print(f"Would apply pfSense rule: {rule.rule_type} for {rule.target}")
    
    def _apply_iptables_rule(self, rule: FirewallRule):
        """Apply rule via iptables."""
        # This would execute iptables commands
        # For now, just log
        print(f"Would apply iptables rule: {rule.rule_type} for {rule.target}")
    
    def _remove_firewall_rule(self, rule: FirewallRule):
        """Remove rule from actual firewall system."""
        # Similar to _apply_firewall_rule but for removal
        print(f"Would remove firewall rule: {rule.id}")
