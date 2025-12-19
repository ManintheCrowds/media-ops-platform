"""Device authentication with certificate-based auth."""

import logging
import jwt
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..config import Config
from ..client import PiAPIClient

logger = logging.getLogger(__name__)


class DeviceAuthenticator:
    """Handles device authentication and token management."""
    
    def __init__(self, config: Config):
        """Initialize device authenticator."""
        self.config = config
        self.current_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
    
    async def authenticate(self) -> bool:
        """Authenticate device and obtain token.
        
        Returns:
            True if authentication successful
        """
        try:
            # If using certificate-based auth, would use certificate here
            # For now, use token from config or refresh if needed
            
            if self._is_token_valid():
                return True
            
            # Refresh token
            async with PiAPIClient(self.config) as client:
                # In a real implementation, this would use certificate-based auth
                # For now, we assume token is provided in config
                self.current_token = self.config.api.auth_token
                
                # Decode token to get expiration (if JWT)
                try:
                    decoded = jwt.decode(
                        self.current_token,
                        options={"verify_signature": False}
                    )
                    exp = decoded.get("exp")
                    if exp:
                        self.token_expires_at = datetime.fromtimestamp(exp)
                except Exception:
                    # Not a JWT or can't decode, assume valid for 1 hour
                    self.token_expires_at = datetime.utcnow() + timedelta(hours=1)
            
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}", exc_info=True)
            return False
    
    def _is_token_valid(self) -> bool:
        """Check if current token is still valid."""
        if not self.current_token:
            return False
        
        if self.token_expires_at:
            return datetime.utcnow() < self.token_expires_at
        
        return True
    
    def get_token(self) -> Optional[str]:
        """Get current authentication token."""
        return self.current_token or self.config.api.auth_token
    
    async def refresh_token(self) -> bool:
        """Refresh authentication token."""
        self.current_token = None
        self.token_expires_at = None
        return await self.authenticate()
