"""API Gateway routes for proxying to services."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response, StreamingResponse
import httpx
from app.models import Service, User
from app.auth.oauth2 import get_current_user, get_db
from sqlalchemy.orm import Session
from services.file_storage.seafile_client import SeafileClient
from services.media_server.jellyfin_client import JellyfinClient
from services.productivity.wiki_client import WikiClient
from services.dev_tools.gitea_client import GiteaClient
from services.monitoring.prometheus_client import PrometheusClient
from services.monitoring.grafana_client import GrafanaClient
from services.security.vaultwarden_client import VaultwardenClient

router = APIRouter()


async def proxy_request(
    service: Service,
    path: str,
    method: str = "GET",
    body: Optional[bytes] = None,
    headers: Optional[Dict[str, str]] = None,
    current_user: Optional[User] = None
) -> Response:
    """Proxy a request to a service."""
    target_url = f"{service.base_url.rstrip('/')}/{path.lstrip('/')}"
    
    # Add authentication if required
    request_headers = headers or {}
    if service.requires_auth and service.auth_token:
        request_headers["Authorization"] = f"Bearer {service.auth_token}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(target_url, headers=request_headers)
            elif method == "POST":
                response = await client.post(target_url, content=body, headers=request_headers)
            elif method == "PUT":
                response = await client.put(target_url, content=body, headers=request_headers)
            elif method == "DELETE":
                response = await client.delete(target_url, headers=request_headers)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Service unavailable: {str(e)}"
        )


@router.get("/file-storage/libraries")
async def get_file_storage_libraries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get file storage libraries."""
    service = db.query(Service).filter(
        Service.service_type == "file_storage",
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="File storage service not found")
    
    async with SeafileClient() as client:
        libraries = await client.get_libraries()
        return {"libraries": libraries}


@router.get("/media-server/libraries")
async def get_media_libraries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get media server libraries."""
    service = db.query(Service).filter(
        Service.service_type == "media_server",
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Media server not found")
    
    async with JellyfinClient() as client:
        libraries = await client.get_libraries()
        return {"libraries": libraries}


@router.get("/media-server/recent")
async def get_recent_media(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recently added media."""
    service = db.query(Service).filter(
        Service.service_type == "media_server",
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Media server not found")
    
    async with JellyfinClient() as client:
        items = await client.get_recent_items(limit)
        return {"items": items}


@router.get("/productivity/pages")
async def get_wiki_pages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get wiki pages."""
    service = db.query(Service).filter(
        Service.service_type == "productivity",
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Productivity service not found")
    
    async with WikiClient() as client:
        pages = await client.get_pages()
        return {"pages": pages}


@router.get("/dev-tools/repositories")
async def get_repositories(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get repositories from Gitea."""
    service = db.query(Service).filter(
        Service.service_type == "dev_tools",
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Development tools service not found")
    
    async with GiteaClient() as client:
        repos = await client.get_repositories(page, limit)
        return {"repositories": repos}


@router.get("/monitoring/metrics")
async def get_monitoring_metrics(
    query: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monitoring metrics from Prometheus."""
    service = db.query(Service).filter(
        Service.service_type == "monitoring",
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Monitoring service not found")
    
    async with PrometheusClient() as client:
        if query:
            result = await client.query(query)
            return {"result": result}
        else:
            metrics = await client.get_metrics()
            return {"metrics": metrics}


@router.get("/monitoring/dashboards")
async def get_grafana_dashboards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Grafana dashboards."""
    service = db.query(Service).filter(
        Service.service_type == "monitoring",
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Monitoring service not found")
    
    async with GrafanaClient() as client:
        dashboards = await client.get_dashboards()
        return {"dashboards": dashboards}


@router.get("/security/stats")
async def get_security_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Vaultwarden statistics (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = db.query(Service).filter(
        Service.service_type == "security",
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Security service not found")
    
    async with VaultwardenClient() as client:
        stats = await client.get_stats()
        return {"stats": stats}


@router.api_route("/proxy/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_to_service(
    service_name: str,
    path: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generic proxy endpoint for any service."""
    service = db.query(Service).filter(
        Service.name == service_name,
        Service.is_active == True
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    body = await request.body() if request.method in ["POST", "PUT"] else None
    headers = dict(request.headers)
    
    # Remove host header to avoid conflicts
    headers.pop("host", None)
    
    return await proxy_request(
        service=service,
        path=path,
        method=request.method,
        body=body,
        headers=headers,
        current_user=current_user
    )


