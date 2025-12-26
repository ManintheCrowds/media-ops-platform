"""Local breach database management for fast lookups."""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..models.breaches import UserBreach, BreachHistory, DomainBreach
from ..config import config

logger = logging.getLogger(__name__)


class BreachDatabase:
    """Local breach database for fast email/domain lookups."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def import_breaches(self, breaches: List[Dict[str, Any]], source: str) -> Dict[str, int]:
        """
        Import breach data into database.
        
        Args:
            breaches: List of normalized breach dictionaries
            source: Source identifier
        
        Returns:
            Dictionary with import statistics
        """
        imported = 0
        updated = 0
        errors = 0
        
        # Group by breach name for efficiency
        breach_groups = {}
        for breach in breaches:
            breach_name = breach.get("breach_name", "Unknown")
            if breach_name not in breach_groups:
                breach_groups[breach_name] = []
            breach_groups[breach_name].append(breach)
        
        # Process each breach group
        for breach_name, breach_list in breach_groups.items():
            try:
                # Get or create breach history
                breach_history = self.db.query(BreachHistory).filter(
                    BreachHistory.breach_name == breach_name
                ).first()
                
                if not breach_history:
                    # Create new breach history
                    breach_history = BreachHistory(
                        breach_name=breach_name,
                        title=breach_name,
                        pwn_count=len(breach_list),
                        data_classes=breach_list[0].get("data_classes", []) if breach_list else [],
                        is_verified=False,
                        breach_metadata={"source": source}
                    )
                    self.db.add(breach_history)
                    self.db.flush()
                
                # Import email breaches
                for breach_data in breach_list:
                    email = breach_data.get("email", "").lower()
                    if not email or '@' not in email:
                        continue
                    
                    # Check if already exists
                    existing = self.db.query(UserBreach).filter(
                        and_(
                            UserBreach.email == email,
                            UserBreach.breach_name == breach_name
                        )
                    ).first()
                    
                    if existing:
                        # Update existing
                        if breach_data.get("breach_date"):
                            try:
                                from dateutil import parser
                                existing.breach_date = parser.parse(breach_data["breach_date"])
                            except:
                                pass
                        existing.data_classes = breach_data.get("data_classes", existing.data_classes)
                        updated += 1
                    else:
                        # Create new
                        breach_date = None
                        if breach_data.get("breach_date"):
                            try:
                                from dateutil import parser
                                breach_date = parser.parse(breach_data["breach_date"])
                            except:
                                pass
                        
                        new_breach = UserBreach(
                            email=email,
                            breach_name=breach_name,
                            breach_date=breach_date,
                            data_classes=breach_data.get("data_classes", ["Email addresses"]),
                            is_verified=breach_data.get("is_verified", False),
                            detected_at=datetime.now(timezone.utc),
                            notified=False,
                            breach_metadata={"source": source, **breach_data.get("metadata", {})}
                        )
                        self.db.add(new_breach)
                        imported += 1
                
            except Exception as e:
                logger.error(f"Error importing breach {breach_name}: {e}")
                errors += 1
        
        try:
            self.db.commit()
            logger.info(f"Imported {imported} new breaches, updated {updated} existing, {errors} errors")
        except Exception as e:
            logger.error(f"Error committing breach imports: {e}")
            self.db.rollback()
            errors += imported + updated
            imported = 0
            updated = 0
        
        return {
            "imported": imported,
            "updated": updated,
            "errors": errors,
            "total_processed": len(breaches)
        }
    
    def lookup_email(self, email: str) -> List[UserBreach]:
        """
        Lookup breaches for an email address.
        
        Args:
            email: Email address to lookup
        
        Returns:
            List of UserBreach records
        """
        return self.db.query(UserBreach).filter(
            UserBreach.email == email.lower()
        ).order_by(UserBreach.detected_at.desc()).all()
    
    def lookup_domain(self, domain: str) -> List[UserBreach]:
        """
        Lookup breaches for a domain (extract from emails).
        
        Args:
            domain: Domain name to lookup
        
        Returns:
            List of UserBreach records for emails in that domain
        """
        domain_lower = domain.lower()
        return self.db.query(UserBreach).filter(
            UserBreach.email.like(f"%@{domain_lower}")
        ).order_by(UserBreach.detected_at.desc()).all()
    
    def get_breach_statistics(self) -> Dict[str, Any]:
        """Get statistics about the breach database."""
        total_breaches = self.db.query(UserBreach).count()
        unique_emails = self.db.query(func.count(func.distinct(UserBreach.email))).scalar() or 0
        unique_breach_names = self.db.query(func.count(func.distinct(UserBreach.breach_name))).scalar() or 0
        
        # Get unique domains
        all_emails = self.db.query(UserBreach.email).distinct().all()
        domains = set()
        for (email,) in all_emails:
            if '@' in email:
                domain = email.split('@')[1]
                domains.add(domain)
        
        return {
            "total_breach_records": total_breaches,
            "unique_emails": unique_emails,
            "unique_breach_names": unique_breach_names,
            "unique_domains": len(domains),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    def get_breach_names(self) -> List[str]:
        """Get list of all breach names in database."""
        breach_names = self.db.query(func.distinct(UserBreach.breach_name)).all()
        return [name[0] for name in breach_names if name[0]]

