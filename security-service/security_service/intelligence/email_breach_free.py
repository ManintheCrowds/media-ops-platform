"""Free email breach detection service using public breach sources."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .public_breach_sources import PublicBreachSources
from ..models.breaches import UserBreach, BreachHistory
from ..config import config

logger = logging.getLogger(__name__)


class EmailBreachServiceFree:
    """Free service for checking emails against public breach database."""
    
    def __init__(self, db: Session):
        self.db = db
        self.public_sources = PublicBreachSources(db)
        self.enabled = config.hibp_enable_email_check
        self.cache_ttl = timedelta(seconds=config.hibp_cache_ttl)
    
    async def check_email(
        self,
        email: str,
        user_id: Optional[int] = None,
        force_refresh: bool = False,
        truncate_response: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Check if email has been breached using public sources.
        
        Args:
            email: Email address to check
            user_id: Optional user ID to associate with breach
            force_refresh: Force refresh from sources (ignore cache)
            truncate_response: Return only breach names (faster, less data)
        
        Returns:
            List of breach dictionaries with breach details
        """
        if not self.enabled:
            logger.debug("Email breach checking is disabled")
            return []
        
        if not email:
            return []
        
        # Check cache first
        if not force_refresh:
            cached_breaches = self.db.query(UserBreach).filter(
                and_(
                    UserBreach.email == email.lower(),
                    UserBreach.detected_at > datetime.now(timezone.utc) - self.cache_ttl
                )
            ).all()
            
            if cached_breaches:
                logger.debug(f"Returning cached breach data for {email}")
                return [self._breach_to_dict(b) for b in cached_breaches]
        
        # Lookup in public breach database
        try:
            breach_data_list = self.public_sources.lookup_email(email)
            
            if not breach_data_list:
                logger.debug(f"No breaches found for {email}")
                return []
            
            # Store breaches in database
            stored_breaches = []
            for breach_data in breach_data_list:
                breach_name = breach_data.get("breach_name", "")
                
                # Check if breach already exists for this email
                existing = self.db.query(UserBreach).filter(
                    and_(
                        UserBreach.email == email.lower(),
                        UserBreach.breach_name == breach_name
                    )
                ).first()
                
                if existing:
                    # Update existing breach record
                    if user_id:
                        existing.user_id = user_id
                    stored_breaches.append(existing)
                else:
                    # Create new breach record
                    breach_date = None
                    if breach_data.get("breach_date"):
                        try:
                            from dateutil import parser
                            breach_date = parser.parse(breach_data["breach_date"])
                        except:
                            pass
                    
                    new_breach = UserBreach(
                        user_id=user_id,
                        email=email.lower(),
                        breach_name=breach_name,
                        breach_date=breach_date,
                        data_classes=breach_data.get("data_classes", ["Email addresses"]),
                        is_verified=breach_data.get("is_verified", False),
                        detected_at=datetime.now(timezone.utc),
                        notified=False,
                        breach_metadata=breach_data
                    )
                    self.db.add(new_breach)
                    stored_breaches.append(new_breach)
                    
                    # Update or create breach history
                    self._update_breach_history(breach_data)
            
            self.db.commit()
            
            # Refresh all stored breaches
            for breach in stored_breaches:
                self.db.refresh(breach)
            
            logger.info(f"Found {len(breach_data_list)} breach(es) for {email}")
            return [self._breach_to_dict(b) for b in stored_breaches]
            
        except Exception as e:
            logger.error(f"Email breach check failed for {email}: {e}")
            self.db.rollback()
            return []
    
    async def check_multiple_emails(
        self,
        emails: List[str],
        user_ids: Optional[Dict[str, int]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Check multiple emails for breaches.
        
        Args:
            emails: List of email addresses to check
            user_ids: Optional mapping of email to user_id
        
        Returns:
            Dictionary mapping email to list of breaches
        """
        results = {}
        user_ids = user_ids or {}
        
        for email in emails:
            user_id = user_ids.get(email)
            breaches = await self.check_email(email, user_id=user_id)
            results[email] = breaches
        
        return results
    
    def _update_breach_history(self, breach_data: Dict[str, Any]) -> None:
        """Update or create breach history record."""
        breach_name = breach_data.get("breach_name", "")
        if not breach_name:
            return
        
        existing = self.db.query(BreachHistory).filter(
            BreachHistory.breach_name == breach_name
        ).first()
        
        if not existing:
            # Create new breach history
            breach_date = None
            if breach_data.get("breach_date"):
                try:
                    from dateutil import parser
                    breach_date = parser.parse(breach_data["breach_date"])
                except:
                    pass
            
            new_history = BreachHistory(
                breach_name=breach_name,
                title=breach_name,
                breach_date=breach_date,
                data_classes=breach_data.get("data_classes", []),
                is_verified=breach_data.get("is_verified", False),
                breach_metadata=breach_data
            )
            self.db.add(new_history)
    
    def _breach_to_dict(self, breach: UserBreach) -> Dict[str, Any]:
        """Convert UserBreach to dictionary."""
        return {
            "id": breach.id,
            "user_id": breach.user_id,
            "email": breach.email,
            "breach_name": breach.breach_name,
            "breach_date": breach.breach_date.isoformat() if breach.breach_date else None,
            "pwn_count": breach.pwn_count,
            "description": breach.description,
            "data_classes": breach.data_classes,
            "is_verified": breach.is_verified,
            "is_sensitive": breach.is_sensitive,
            "detected_at": breach.detected_at.isoformat() if breach.detected_at else None,
            "notified": breach.notified
        }
    
    def get_user_breaches(self, user_id: int) -> List[UserBreach]:
        """Get all breaches for a user."""
        return self.db.query(UserBreach).filter(
            UserBreach.user_id == user_id
        ).order_by(UserBreach.detected_at.desc()).all()
    
    def get_email_breaches(self, email: str) -> List[UserBreach]:
        """Get all breaches for an email address."""
        return self.db.query(UserBreach).filter(
            UserBreach.email == email.lower()
        ).order_by(UserBreach.detected_at.desc()).all()

