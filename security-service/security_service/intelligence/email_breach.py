"""Email breach detection service using free public breach sources."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..intelligence.email_breach_free import EmailBreachServiceFree
from ..models.breaches import UserBreach, BreachHistory
from ..config import config

logger = logging.getLogger(__name__)


class EmailBreachService:
    """Service for checking emails against public breach database (free)."""
    
    def __init__(self, db: Session):
        self.db = db
        self.free_service = EmailBreachServiceFree(db)
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
        Check if email has been breached.
        
        Args:
            email: Email address to check
            user_id: Optional user ID to associate with breach
            force_refresh: Force refresh from API (ignore cache)
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
        
        # Use free public breach sources service
        try:
            breaches = await self.free_service.check_email(
                email,
                user_id=user_id,
                force_refresh=force_refresh,
                truncate_response=truncate_response
            )
            
            return breaches
            
        except Exception as e:
            logger.error(f"Email breach check failed for {email}: {e}")
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
        return await self.free_service.check_multiple_emails(emails, user_ids)
    
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

