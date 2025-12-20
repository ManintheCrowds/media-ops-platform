"""Pydantic schemas for project management."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.project import ProjectStatus
from app.schemas.content import ContentItemResponse


class ProjectBase(BaseModel):
    """Base project schema."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = None
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.DRAFT
    metadata: Optional[Dict[str, Any]] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    organization_id: int


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: int
    organization_id: int
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProjectWithContentResponse(ProjectResponse):
    """Schema for project response with content items."""
    content_items: List[ContentItemResponse] = []
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Schema for paginated project list response."""
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    pages: int


