"""Free domain breach monitoring service using public breach sources."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .public_breach_sources import PublicBreachSources
from ..models.breaches import DomainBreach
from ..config import config

logger = logging.getLogger(__name__)


class DomainBreachServiceFree:
    """Free service for monitoring domain breaches using public sources."""
    
    def __init__(self, db: Session):
        self.db = db
        self.public_sources = PublicBreachSources(db)
        self.monitored_domains = getattr(config, 'breach_monitored_domains', config.hibp_monitored_domains)
        self.cache_ttl = timedelta(seconds=config.hibp_domain_check_interval)
    
    async def check_domain(self, domain: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Check domain for breached email addresses using public sources.
        
        Args:
            domain: Domain name to check
            force_refresh: Force refresh from sources (ignore cache)
        
        Returns:
            List of breach dictionaries for the domain
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
        
        # Lookup in public breach database
        try:
            breach_data_list = self.public_sources.lookup_domain(domain)
            
            if not breach_data_list:
                logger.debug(f"No breaches found for domain {domain}")
                # Update last_checked even if no breaches
                self._update_domain_breach(domain, [])
                return []
            
            # Convert to email list format
            affected_emails = []
            breach_names = set()
            
            for breach_group in breach_data_list:
                breach_name = breach_group.get("breach_name", "")
                breach_names.add(breach_name)
                emails = breach_group.get("emails", [])
                affected_emails.extend([
                    {
                        "email": email,
                        "Breaches": [{"Name": breach_name}]
                    }
                    for email in emails
                ])
            
            # Store domain breach information
            self._update_domain_breach(domain, list(breach_names), affected_emails)
            
            logger.info(f"Found {len(affected_emails)} breached email(s) for domain {domain}")
            return affected_emails
            
        except Exception as e:
            logger.error(f"Domain breach check failed for {domain}: {e}")
            return []
    
    def _update_domain_breach(
        self,
        domain: str,
        breach_names: List[str],
        affected_emails: Optional[List[Any]] = None
    ) -> None:
        """Update or create domain breach record."""
        domain_lower = domain.lower()
        affected_emails = affected_emails or []
        
        # For each breach name, create/update a DomainBreach record
        for breach_name in breach_names:
            if not breach_name:
                continue
            
            existing = self.db.query(DomainBreach).filter(
                and_(
                    DomainBreach.domain == domain_lower,
                    DomainBreach.breach_name == breach_name
                )
            ).first()
            
            if existing:
                # Update existing
                existing.affected_emails = len(affected_emails)
                existing.affected_email_list = affected_emails
                existing.last_checked = datetime.now(timezone.utc)
            else:
                # Create new
                new_breach = DomainBreach(
                    domain=domain_lower,
                    breach_name=breach_name,
                    affected_emails=len(affected_emails),
                    affected_email_list=affected_emails,
                    detected_at=datetime.now(timezone.utc),
                    last_checked=datetime.now(timezone.utc),
                    notified=False
                )
                self.db.add(new_breach)
        
        self.db.commit()
    
    async def monitor_all_domains(self) -> Dict[str, Any]:
        """
        Monitor all configured domains for breaches.
        
        Returns:
            Dictionary with monitoring results
        """
        if not self.monitored_domains:
            logger.info("No domains configured for monitoring")
            return {
                "monitored": 0,
                "breaches_found": 0,
                "new_breaches": 0
            }
        
        total_breaches = 0
        new_breaches = 0
        
        logger.info(f"Monitoring {len(self.monitored_domains)} domain(s) for breaches")
        
        for domain in self.monitored_domains:
            try:
                # Check if domain has been checked recently
                recent_check = self.db.query(DomainBreach).filter(
                    DomainBreach.domain == domain.lower()
                ).order_by(DomainBreach.last_checked.desc()).first()
                
                # Skip if checked recently
                if recent_check and recent_check.last_checked:
                    if recent_check.last_checked > datetime.now(timezone.utc) - self.cache_ttl:
                        continue
                
                # Check domain
                breached_emails = await self.check_domain(domain, force_refresh=True)
                
                if breached_emails:
                    total_breaches += len(breached_emails)
                    
                    # Check for new breaches (not notified)
                    domain_breaches = self.db.query(DomainBreach).filter(
                        DomainBreach.domain == domain.lower(),
                        DomainBreach.notified == False
                    ).all()
                    
                    new_breaches += len(domain_breaches)
                    
                    logger.info(f"Domain {domain}: {len(breached_emails)} breached email(s) found")
                
            except Exception as e:
                logger.error(f"Error monitoring domain {domain}: {e}")
        
        logger.info(f"Domain monitoring completed: {total_breaches} breaches found, {new_breaches} new")
        
        return {
            "monitored": len(self.monitored_domains),
            "breaches_found": total_breaches,
            "new_breaches": new_breaches
        }
    
    def get_domain_breaches(self, domain: str) -> List[DomainBreach]:
        """Get all breach records for a domain."""
        return self.db.query(DomainBreach).filter(
            DomainBreach.domain == domain.lower()
        ).order_by(DomainBreach.detected_at.desc()).all()
    
    def get_unnotified_breaches(self, limit: int = 100) -> List[DomainBreach]:
        """Get domain breaches that haven't been notified yet."""
        return self.db.query(DomainBreach).filter(
            DomainBreach.notified == False
        ).order_by(DomainBreach.detected_at.desc()).limit(limit).all()
    
    def mark_breach_notified(self, breach_id: int) -> bool:
        """Mark a domain breach as notified."""
        try:
            breach = self.db.query(DomainBreach).filter(DomainBreach.id == breach_id).first()
            if breach:
                breach.notified = True
                breach.notified_at = datetime.now(timezone.utc)
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to mark domain breach {breach_id} as notified: {e}")
            self.db.rollback()
            return False

