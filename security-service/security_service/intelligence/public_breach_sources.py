"""Public breach sources aggregation service."""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from .breach_data_downloader import BreachDataDownloader
from .breach_database import BreachDatabase
from ..config import config

logger = logging.getLogger(__name__)


class PublicBreachSources:
    """Service for aggregating breach data from multiple free public sources."""
    
    def __init__(self, db: Session):
        self.db = db
        self.downloader = BreachDataDownloader()
        self.database = BreachDatabase(db)
        self.update_interval = timedelta(seconds=config.breach_data_update_interval)
        self.last_update = None
    
    async def update_breach_database(self, force: bool = False) -> Dict[str, Any]:
        """
        Update breach database from public sources.
        
        Args:
            force: Force update even if recently updated
        
        Returns:
            Dictionary with update statistics
        """
        # Check if update is needed
        if not force and self.last_update:
            if datetime.now(timezone.utc) - self.last_update < self.update_interval:
                logger.debug("Breach database recently updated, skipping")
                return {
                    "updated": False,
                    "reason": "Recently updated",
                    "last_update": self.last_update.isoformat()
                }
        
        try:
            logger.info("Updating breach database from public sources")
            
            # Download from all sources
            breaches = await self.downloader.download_all_sources()
            
            if not breaches:
                logger.warning("No breach data downloaded from sources")
                return {
                    "updated": False,
                    "reason": "No data downloaded",
                    "breaches_downloaded": 0
                }
            
            # Import into database
            import_stats = self.database.import_breaches(breaches, "public_sources")
            
            self.last_update = datetime.now(timezone.utc)
            
            return {
                "updated": True,
                "breaches_downloaded": len(breaches),
                "import_stats": import_stats,
                "last_update": self.last_update.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating breach database: {e}")
            return {
                "updated": False,
                "error": str(e)
            }
    
    def lookup_email(self, email: str) -> List[Dict[str, Any]]:
        """
        Lookup breaches for an email address.
        
        Args:
            email: Email address to check
        
        Returns:
            List of breach dictionaries
        """
        breaches = self.database.lookup_email(email)
        
        return [
            {
                "email": b.email,
                "breach_name": b.breach_name,
                "breach_date": b.breach_date.isoformat() if b.breach_date else None,
                "data_classes": b.data_classes or [],
                "is_verified": b.is_verified,
                "detected_at": b.detected_at.isoformat() if b.detected_at else None
            }
            for b in breaches
        ]
    
    def lookup_domain(self, domain: str) -> List[Dict[str, Any]]:
        """
        Lookup breaches for a domain.
        
        Args:
            domain: Domain name to check
        
        Returns:
            List of breach dictionaries for emails in that domain
        """
        breaches = self.database.lookup_domain(domain)
        
        # Group by breach name
        breach_groups = {}
        for breach in breaches:
            breach_name = breach.breach_name
            if breach_name not in breach_groups:
                breach_groups[breach_name] = {
                    "breach_name": breach_name,
                    "emails": [],
                    "breach_date": breach.breach_date.isoformat() if breach.breach_date else None,
                    "data_classes": breach.data_classes or []
                }
            breach_groups[breach_name]["emails"].append(breach.email)
        
        return list(breach_groups.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get breach database statistics."""
        return self.database.get_breach_statistics()

