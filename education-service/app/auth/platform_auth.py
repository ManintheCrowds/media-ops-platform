"""Platform authentication integration."""

from typing import Optional
from jose import JWTError, jwt
import httpx
from pydantic import BaseModel
from app.config import settings


class UserInfo(BaseModel):
    """User information from platform token."""
    sub: str  # username
    email: Optional[str] = None
    is_admin: bool = False
    is_active: bool = True


async def validate_platform_token(token: str) -> Optional[UserInfo]:
    """
    Validate JWT token from main platform.
    
    First tries to validate locally with shared secret,
    then falls back to calling platform API.
    """
    # Option 1: Validate locally with shared secret
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return UserInfo(
            sub=payload.get("sub"),
            email=payload.get("email"),
            is_admin=payload.get("is_admin", False),
            is_active=payload.get("is_active", True),
        )
    except JWTError:
        pass
    
    # Option 2: Call main platform API for validation
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.platform_url}/api/auth/validate",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                data = response.json()
                return UserInfo(**data)
    except Exception:
        pass
    
    return None


def get_oauth2_scheme():
    """Get OAuth2 password bearer scheme."""
    from fastapi.security import OAuth2PasswordBearer
    return OAuth2PasswordBearer(tokenUrl=f"{settings.platform_url}/api/auth/token")







