"""Access control policies."""

from datetime import datetime, time
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..models.threats import FirewallRule


class AccessControlPolicy:
    """Access control policy definition."""
    
    def __init__(self, policy_id: str, name: str, enabled: bool = True):
        self.policy_id = policy_id
        self.name = name
        self.enabled = enabled
        self.ip_whitelist: List[str] = []
        self.ip_blacklist: List[str] = []
        self.allowed_time_ranges: List[Dict[str, time]] = []
        self.blocked_countries: List[str] = []
        self.require_mfa: bool = False
    
    def is_ip_allowed(self, ip_address: str) -> bool:
        """Check if IP is allowed."""
        if not self.enabled:
            return True
        
        # Check whitelist (takes precedence)
        if self.ip_whitelist and ip_address in self.ip_whitelist:
            return True
        
        # Check blacklist
        if ip_address in self.ip_blacklist:
            return False
        
        return True
    
    def is_time_allowed(self, check_time: Optional[datetime] = None) -> bool:
        """Check if current time is within allowed range."""
        if not self.enabled or not self.allowed_time_ranges:
            return True
        
        if check_time is None:
            check_time = datetime.now()
        
        current_time = check_time.time()
        
        for time_range in self.allowed_time_ranges:
            start = time_range.get("start")
            end = time_range.get("end")
            
            if start and end:
                if start <= end:  # Normal range (e.g., 9:00 - 17:00)
                    if start <= current_time <= end:
                        return True
                else:  # Overnight range (e.g., 22:00 - 6:00)
                    if current_time >= start or current_time <= end:
                        return True
        
        return False


class AccessControlEngine:
    """Access control policy enforcement engine."""
    
    def __init__(self, db: Session):
        self.db = db
        self.policies: Dict[str, AccessControlPolicy] = {}
        self._load_policies()
    
    def _load_policies(self):
        """Load access control policies."""
        # Load from database or configuration
        # For now, create default policy
        default_policy = AccessControlPolicy("default", "Default Access Policy")
        self.policies["default"] = default_policy
    
    def check_access(self, ip_address: str, user_id: Optional[int] = None,
                    endpoint: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if access is allowed.
        Returns: (allowed, reason)
        """
        # Check firewall rules first
        firewall_rules = self.db.query(FirewallRule).filter(
            FirewallRule.target == ip_address,
            FirewallRule.is_active == "true",
            FirewallRule.action == "block"
        ).first()
        
        if firewall_rules:
            return False, "IP address is blocked by firewall rule"
        
        # Check policies
        for policy in self.policies.values():
            if not policy.is_ip_allowed(ip_address):
                return False, f"IP address not allowed by policy: {policy.name}"
            
            if not policy.is_time_allowed():
                return False, f"Access not allowed at current time by policy: {policy.name}"
        
        return True, None
    
    def add_ip_to_whitelist(self, policy_id: str, ip_address: str):
        """Add IP to whitelist."""
        if policy_id in self.policies:
            policy = self.policies[policy_id]
            if ip_address not in policy.ip_whitelist:
                policy.ip_whitelist.append(ip_address)
    
    def add_ip_to_blacklist(self, policy_id: str, ip_address: str):
        """Add IP to blacklist."""
        if policy_id in self.policies:
            policy = self.policies[policy_id]
            if ip_address not in policy.ip_blacklist:
                policy.ip_blacklist.append(ip_address)
    
    def get_policy(self, policy_id: str) -> Optional[AccessControlPolicy]:
        """Get access control policy."""
        return self.policies.get(policy_id)
    
    def create_policy(self, policy: AccessControlPolicy):
        """Create new access control policy."""
        self.policies[policy.policy_id] = policy
