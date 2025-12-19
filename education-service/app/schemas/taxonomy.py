"""Pydantic schemas for taxonomy and tagging."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TagBase(BaseModel):
    """Base tag schema."""
    name: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=50)


class TagCreate(TagBase):
    """Schema for creating a tag."""
    pass


class TagResponse(TagBase):
    """Schema for tag response."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TaxonomyNodeBase(BaseModel):
    """Base taxonomy node schema."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = None
    parent_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class TaxonomyNodeCreate(TaxonomyNodeBase):
    """Schema for creating a taxonomy node."""
    pass


class TaxonomyNodeUpdate(BaseModel):
    """Schema for updating a taxonomy node."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = None
    parent_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class TaxonomyNodeResponse(TaxonomyNodeBase):
    """Schema for taxonomy node response."""
    id: int
    level: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TaxonomyTreeResponse(TaxonomyNodeResponse):
    """Schema for taxonomy tree with children."""
    children: List["TaxonomyTreeResponse"] = []
    
    class Config:
        from_attributes = True


TaxonomyTreeResponse.model_rebuild()
