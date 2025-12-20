"""Content management API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, UserInfo
from app.models.content import ContentType
from app.schemas.content import (
    ContentItemCreate,
    ContentItemUpdate,
    ContentItemResponse,
    ContentVersionResponse,
    ContentListResponse,
)
from app.services.content_service import ContentService

router = APIRouter()


@router.post("/content", response_model=ContentItemResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_data: ContentItemCreate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Create a new content item."""
    content = ContentService.create_content(db, content_data, current_user)
    return ContentItemResponse.model_validate(content)


@router.get("/content", response_model=ContentListResponse)
async def list_content(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    content_type: Optional[ContentType] = Query(None, description="Filter by content type"),
    search: Optional[str] = Query(None, description="Search in title, description, and body"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """List content items with filtering and pagination."""
    items, total = ContentService.list_content(
        db, project_id, content_type, search, page, page_size
    )
    
    pages = (total + page_size - 1) // page_size
    
    return ContentListResponse(
        items=[ContentItemResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/content/{content_id}", response_model=ContentItemResponse)
async def get_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Get a specific content item."""
    content = ContentService.get_content(db, content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    return ContentItemResponse.model_validate(content)


@router.put("/content/{content_id}", response_model=ContentItemResponse)
async def update_content(
    content_id: int,
    content_data: ContentItemUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Update a content item."""
    content = ContentService.update_content(db, content_id, content_data, current_user)
    return ContentItemResponse.model_validate(content)


@router.delete("/content/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Delete a content item."""
    ContentService.delete_content(db, content_id)
    return None


@router.get("/content/{content_id}/versions", response_model=list[ContentVersionResponse])
async def list_versions(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """List all versions of a content item."""
    # Verify content exists
    content = ContentService.get_content(db, content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    versions = ContentService.get_versions(db, content_id)
    return [ContentVersionResponse.model_validate(v) for v in versions]


@router.get("/content/{content_id}/versions/{version_number}", response_model=ContentVersionResponse)
async def get_version(
    content_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Get a specific version of a content item."""
    version = ContentService.get_version(db, content_id, version_number)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    return ContentVersionResponse.model_validate(version)


@router.post("/content/{content_id}/revert/{version_number}", response_model=ContentItemResponse)
async def revert_to_version(
    content_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Revert content item to a specific version."""
    content = ContentService.revert_to_version(db, content_id, version_number, current_user)
    return ContentItemResponse.model_validate(content)



