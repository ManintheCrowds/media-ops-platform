"""Pydantic schemas for content management."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.content import ContentType


class ContentItemBase(BaseModel):
    """Base content item schema."""
    title: str = Field(..., min_length=1, max_length=500)
    slug: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
    content_type: ContentType
    metadata: Optional[Dict[str, Any]] = None
    external_refs: Optional[Dict[str, Any]] = None
    parent_id: Optional[int] = None


class ContentItemCreate(ContentItemBase):
    """Schema for creating content item."""
    project_id: int


class ContentItemUpdate(BaseModel):
    """Schema for updating content item."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    body: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    external_refs: Optional[Dict[str, Any]] = None
    parent_id: Optional[int] = None


class ContentItemResponse(ContentItemBase):
    """Schema for content item response."""
    id: int
    project_id: int
    version: int
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ContentVersionResponse(BaseModel):
    """Schema for content version response."""
    id: int
    content_item_id: int
    version_number: int
    title: str
    body: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_by: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ContentListResponse(BaseModel):
    """Schema for paginated content list response."""
    items: List[ContentItemResponse]
    total: int
    page: int
    page_size: int
    pages: int

