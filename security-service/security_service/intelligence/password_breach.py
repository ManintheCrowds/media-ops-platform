"""Password breach checking service using HIBP Pwned Passwords API."""

import logging
from typing import Optional, Tuple
from ..intelligence.hibp import HIBPClient
from ..config import config

logger = logging.getLogger(__name__)


class PasswordBreachService:
    """Service for checking passwords against HIBP Pwned Passwords database."""
    
    def __init__(self):
        self.client = HIBPClient()
        self.enabled = config.hibp_enable_password_check
    
    async def check_password(self, password: str) -> Tuple[bool, int]:
        """
        Check if password has been pwned.
        
        Args:
            password: Plain text password to check
        
        Returns:
            Tuple of (is_breached: bool, breach_count: int)
            - is_breached: True if password found in breach database
            - breach_count: Number of times password appears (0 if not found)
        """
        if not self.enabled:
            logger.debug("Password breach checking is disabled")
            return False, 0
        
        if not password:
            return False, 0
        
        try:
            breach_count = await self.client.check_password(password)
            is_breached = breach_count > 0
            
            if is_breached:
                logger.warning(f"Password found in breach database ({breach_count} occurrences)")
            else:
                logger.debug("Password not found in breach database")
            
            return is_breached, breach_count
            
        except Exception as e:
            logger.error(f"Password breach check failed: {e}")
            # Fail open - don't block registration if service is unavailable
            return False, 0
    
    async def validate_password(self, password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password and return whether it's safe to use.
        
        Args:
            password: Plain text password to validate
        
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
            - is_valid: True if password is safe to use
            - error_message: Error message if password is breached
        """
        is_breached, breach_count = await self.check_password(password)
        
        if is_breached:
            error_message = (
                f"This password has been found in {breach_count:,} data breach(es). "
                "Please choose a different password for your security."
            )
            return False, error_message
        
        return True, None

