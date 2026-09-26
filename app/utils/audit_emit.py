"""Best-effort audit event emission to security-service."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def emit_audit_event(
    event_type: str,
    action: str,
    *,
    success: bool = True,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """POST an audit event to security-service; never raise to callers."""
    base = (settings.security_service_url or "").rstrip("/")
    if not base:
        return

    payload: Dict[str, Any] = {
        "event_type": event_type,
        "action": action,
        "success": success,
        "user_id": user_id,
        "username": username,
        "ip_address": ip_address,
        "details": details or {},
    }
    try:
        with httpx.Client(timeout=settings.security_audit_timeout_seconds) as client:
            response = client.post(f"{base}/api/security/audit", json=payload)
            if response.status_code >= 400:
                logger.warning(
                    "Audit emit failed: status=%s body=%s",
                    response.status_code,
                    response.text[:200],
                )
    except Exception as exc:  # noqa: BLE001 — best-effort side channel
        logger.warning("Audit emit unavailable: %s", exc)
