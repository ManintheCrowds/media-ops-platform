"""Device-scoped JWT helpers for Pi clients."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings

DEVICE_TOKEN_USE = "device"


class DevicePrincipal(BaseModel):
    """Authenticated device principal."""

    device_id: str
    token_use: str = DEVICE_TOKEN_USE


def create_device_token(device_id: str, expires_minutes: int = 60 * 24 * 30) -> str:
    """Mint a device-scoped JWT."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {
        "sub": device_id,
        "device_id": device_id,
        "token_use": DEVICE_TOKEN_USE,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_device_token(token: str) -> Optional[DevicePrincipal]:
    """Decode and validate a device JWT; return None if not a device token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        return None

    if payload.get("token_use") != DEVICE_TOKEN_USE:
        return None

    device_id = payload.get("device_id") or payload.get("sub")
    if not device_id:
        return None

    return DevicePrincipal(device_id=str(device_id))
