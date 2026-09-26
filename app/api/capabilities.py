"""Platform capabilities discovery API."""

from typing import Any, Dict

from fastapi import APIRouter

from app.config import settings

router = APIRouter()

SYNC_PROTOCOL_VERSION = "1"


@router.get("")
async def get_capabilities() -> Dict[str, Any]:
    """Machine-readable capabilities for harness clients and Pi sync."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "auth": {
            "methods": ["oauth2_password", "jwt"],
            "token_path": "/api/auth/token",
            "validate_path": "/api/auth/validate",
            "device_token_required_for_pi_sync": True,
        },
        "gateway": {
            "service_types": [
                "file_storage",
                "media_server",
                "productivity",
                "dev_tools",
                "monitoring",
                "security",
            ],
            "proxy_path": "/api/gateway/proxy/{service_name}/{path}",
        },
        "sync": {
            "protocol_version": SYNC_PROTOCOL_VERSION,
            "education_base_path": "/api/v1/pi",
            "download_mode": "stream",
            "package_states": ["pending", "ready", "expired", "failed"],
        },
        "features": {
            "capabilities": True,
            "audit_emit": True,
            "share_dto": False,
            "oidc": False,
        },
    }
