"""Domain breach monitoring service using free public breach sources."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..intelligence.domain_breach_free import DomainBreachServiceFree
from ..models.breaches import DomainBreach
from ..config import config

logger = logging.getLogger(__name__)


class DomainBreachService:
    """Service for monitoring domain breaches using free public sources."""
    
    def __init__(self, db: Session):
        self.db = db
        self.free_service = DomainBreachServiceFree(db)
        self.monitored_domains = getattr(config, 'breach_monitored_domains', config.hibp_monitored_domains)
        self.cache_ttl = timedelta(seconds=config.hibp_domain_check_interval)
    
    async def check_domain(self, domain: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Check domain for breached email addresses.
        
        Args:
            domain: Domain name to check
            force_refresh: Force refresh from API (ignore cache)
        
        Returns:
            List of breached email addresses with breach details
        """
        if not domain:
            return []
        
        # Check cache first
        if not force_refresh:
            cached = self.db.query(DomainBreach).filter(
                and_(
                    DomainBreach.domain == domain.lower(),
                    DomainBreach.last_checked > datetime.now(timezone.utc) - self.cache_ttl
                )
            ).first()
            
            if cached:
                logger.debug(f"Returning cached domain breach data for {domain}")
                return cached.affected_email_list or []
        
        # Use free public breach sources service
        try:
            breached_emails = await self.free_service.check_domain(domain, force_refresh=force_refresh)
            return breached_emails
            
        except Exception as e:
            logger.error(f"Domain breach check failed for {domain}: {e}")
            return []
    
    async def monitor_all_domains(self) -> Dict[str, Any]:
        """
        Monitor all configured domains for breaches.
        
        Returns:
            Dictionary with monitoring results
        """
        return await self.free_service.monitor_all_domains()
    
    def get_domain_breaches(self, domain: str) -> List[DomainBreach]:
        """Get all breach records for a domain."""
        return self.free_service.get_domain_breaches(domain)
    
    def get_unnotified_breaches(self, limit: int = 100) -> List[DomainBreach]:
        """Get domain breaches that haven't been notified yet."""
        return self.free_service.get_unnotified_breaches(limit)
    
    def mark_breach_notified(self, breach_id: int) -> bool:
        """Mark a domain breach as notified."""
        return self.free_service.mark_breach_notified(breach_id)

