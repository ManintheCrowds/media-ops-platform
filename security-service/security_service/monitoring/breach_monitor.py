"""Periodic breach monitoring service for scheduled email checks."""

import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from ..intelligence.email_breach import EmailBreachService
from ..models.breaches import UserBreach
from ..config import config

logger = logging.getLogger(__name__)


class BreachMonitor:
    """Service for periodically monitoring user emails for breaches."""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_breach_service = EmailBreachService(db)
        self.enabled = config.hibp_enable_email_check
    
    async def scan_all_users(self, user_model_class, batch_size: int = 100) -> dict:
        """
        Scan all active user emails for breaches.
        
        Args:
            user_model_class: User model class to query
            batch_size: Number of emails to process per batch
        
        Returns:
            Dictionary with scan statistics
        """
        if not self.enabled:
            logger.info("Breach monitoring is disabled")
            return {
                "enabled": False,
                "scanned": 0,
                "breaches_found": 0,
                "errors": 0
            }
        
        try:
            # Query all active users with emails
            users = self.db.query(user_model_class).filter(
                user_model_class.is_active == True,
                user_model_class.email.isnot(None)
            ).all()
            
            total_users = len(users)
            breaches_found = 0
            errors = 0
            new_breaches = 0
            
            logger.info(f"Starting breach scan for {total_users} users")
            
            # Process in batches to respect rate limits
            for i in range(0, total_users, batch_size):
                batch = users[i:i + batch_size]
                
                for user in batch:
                    try:
                        # Check if email has been checked recently (within cache TTL)
                        recent_check = self.db.query(UserBreach).filter(
                            UserBreach.email == user.email.lower()
                        ).order_by(UserBreach.detected_at.desc()).first()
                        
                        # Skip if checked recently (within cache TTL)
                        if recent_check and recent_check.detected_at:
                            from datetime import timedelta
                            cache_ttl = timedelta(seconds=config.hibp_cache_ttl)
                            if recent_check.detected_at > datetime.now(timezone.utc) - cache_ttl:
                                continue
                        
                        # Check email for breaches
                        breaches = await self.email_breach_service.check_email(
                            user.email,
                            user_id=user.id,
                            force_refresh=True,
                            truncate_response=True
                        )
                        
                        if breaches:
                            breaches_found += len(breaches)
                            # Check if any are new (not notified)
                            for breach in breaches:
                                breach_record = self.db.query(UserBreach).filter(
                                    UserBreach.email == user.email.lower(),
                                    UserBreach.breach_name == breach.get("breach_name")
                                ).first()
                                
                                if breach_record and not breach_record.notified:
                                    new_breaches += 1
                            
                            logger.info(f"Found {len(breaches)} breach(es) for user {user.id} ({user.email})")
                        
                        # Rate limiting delay between requests
                        await asyncio.sleep(config.hibp_rate_limit_delay)
                        
                    except Exception as e:
                        errors += 1
                        logger.error(f"Error checking breaches for user {user.id} ({user.email}): {e}")
                
                logger.info(f"Processed batch {i // batch_size + 1} ({min(i + batch_size, total_users)}/{total_users} users)")
            
            logger.info(f"Breach scan completed: {breaches_found} breaches found, {new_breaches} new, {errors} errors")
            
            return {
                "enabled": True,
                "scanned": total_users,
                "breaches_found": breaches_found,
                "new_breaches": new_breaches,
                "errors": errors,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Breach scan failed: {e}")
            return {
                "enabled": True,
                "scanned": 0,
                "breaches_found": 0,
                "errors": 1,
                "error_message": str(e)
            }
    
    async def scan_specific_emails(self, emails: List[str], user_ids: Optional[dict] = None) -> dict:
        """
        Scan specific email addresses for breaches.
        
        Args:
            emails: List of email addresses to check
            user_ids: Optional mapping of email to user_id
        
        Returns:
            Dictionary with scan results
        """
        if not self.enabled:
            return {
                "enabled": False,
                "scanned": 0,
                "breaches_found": 0
            }
        
        user_ids = user_ids or {}
        results = await self.email_breach_service.check_multiple_emails(emails, user_ids)
        
        total_breaches = sum(len(breaches) for breaches in results.values())
        
        return {
            "enabled": True,
            "scanned": len(emails),
            "breaches_found": total_breaches,
            "results": results
        }
    
    def get_unnotified_breaches(self, limit: int = 100) -> List[UserBreach]:
        """
        Get breaches that haven't been notified yet.
        
        Args:
            limit: Maximum number of breaches to return
        
        Returns:
            List of UserBreach records
        """
        return self.db.query(UserBreach).filter(
            UserBreach.notified == False
        ).order_by(UserBreach.detected_at.desc()).limit(limit).all()
    
    def mark_breach_notified(self, breach_id: int) -> bool:
        """
        Mark a breach as notified.
        
        Args:
            breach_id: ID of the breach to mark
        
        Returns:
            True if successful, False otherwise
        """
        try:
            breach = self.db.query(UserBreach).filter(UserBreach.id == breach_id).first()
            if breach:
                breach.notified = True
                breach.notified_at = datetime.now(timezone.utc)
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to mark breach {breach_id} as notified: {e}")
            self.db.rollback()
            return False

