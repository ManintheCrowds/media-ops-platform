"""Integration API endpoints for linking content to external services."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.dependencies import get_current_user, UserInfo
from app.services.content_service import ContentService
from app.services.integrations.bookstack_client import BookStackClient
from app.services.integrations.gitea_client import GiteaClient
from app.services.integrations.seafile_client import SeafileClient
from app.services.integrations.jellyfin_client import JellyfinClient

router = APIRouter()


class LinkRequest(BaseModel):
    """Request schema for linking content to external service."""
    content_id: int
    external_id: str
    metadata: Optional[Dict[str, Any]] = None


@router.post("/bookstack/link", status_code=status.HTTP_200_OK)
async def link_bookstack(
    request: LinkRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Link content to a BookStack page."""
    content = ContentService.get_content(db, request.content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Fetch BookStack page to verify it exists
    async with BookStackClient() as client:
        page = await client.get_page(int(request.external_id))
        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BookStack page not found"
            )
    
    # Update external_refs
    if not content.external_refs:
        content.external_refs = {}
    
    content.external_refs["bookstack"] = {
        "page_id": int(request.external_id),
        "book_id": page.get("book_id"),
        "metadata": request.metadata or {}
    }
    
    db.commit()
    db.refresh(content)
    
    return {"status": "linked", "content_id": content.id, "external_ref": content.external_refs.get("bookstack")}


@router.post("/gitea/link", status_code=status.HTTP_200_OK)
async def link_gitea(
    request: LinkRequest,
    owner: str,
    repo: str,
    branch: Optional[str] = "main",
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Link content to a Gitea repository."""
    content = ContentService.get_content(db, request.content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Fetch Gitea repository to verify it exists
    async with GiteaClient() as client:
        repo_data = await client.get_repository(owner, repo)
        if not repo_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gitea repository not found"
            )
    
    # Update external_refs
    if not content.external_refs:
        content.external_refs = {}
    
    content.external_refs["gitea"] = {
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "repo_id": repo_data.get("id"),
        "metadata": request.metadata or {}
    }
    
    db.commit()
    db.refresh(content)
    
    return {"status": "linked", "content_id": content.id, "external_ref": content.external_refs.get("gitea")}


@router.post("/seafile/link", status_code=status.HTTP_200_OK)
async def link_seafile(
    request: LinkRequest,
    library_id: str,
    file_path: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Link content to a Seafile library file."""
    content = ContentService.get_content(db, request.content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Verify Seafile library and file exist
    async with SeafileClient() as client:
        library = await client.get_library(library_id)
        if not library:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seafile library not found"
            )
        
        file_info = await client.get_file_info(library_id, file_path)
        if not file_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seafile file not found"
            )
    
    # Update external_refs
    if not content.external_refs:
        content.external_refs = {}
    
    content.external_refs["seafile"] = {
        "library_id": library_id,
        "file_path": file_path,
        "metadata": request.metadata or {}
    }
    
    db.commit()
    db.refresh(content)
    
    return {"status": "linked", "content_id": content.id, "external_ref": content.external_refs.get("seafile")}


@router.post("/jellyfin/link", status_code=status.HTTP_200_OK)
async def link_jellyfin(
    request: LinkRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Link content to a Jellyfin media item."""
    content = ContentService.get_content(db, request.content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Verify Jellyfin item exists
    async with JellyfinClient() as client:
        item = await client.get_item(request.external_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Jellyfin item not found"
            )
    
    # Update external_refs
    if not content.external_refs:
        content.external_refs = {}
    
    content.external_refs["jellyfin"] = {
        "item_id": request.external_id,
        "media_type": item.get("Type"),
        "metadata": request.metadata or {}
    }
    
    db.commit()
    db.refresh(content)
    
    return {"status": "linked", "content_id": content.id, "external_ref": content.external_refs.get("jellyfin")}


@router.get("/external/{service}/{external_id}")
async def fetch_external_resource(
    service: str,
    external_id: str,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Fetch external resource from integrated service."""
    if service == "bookstack":
        async with BookStackClient() as client:
            page = await client.get_page(int(external_id))
            if page:
                return page
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    
    elif service == "gitea":
        # Gitea requires owner/repo, so this endpoint is limited
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use /gitea/link endpoint with owner and repo parameters"
        )
    
    elif service == "seafile":
        async with SeafileClient() as client:
            library = await client.get_library(external_id)
            if library:
                return library
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    
    elif service == "jellyfin":
        async with JellyfinClient() as client:
            item = await client.get_item(external_id)
            if item:
                return item
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown service: {service}"
        )
