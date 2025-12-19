"""Taxonomy and tagging API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, get_current_admin_user, UserInfo
from app.schemas.taxonomy import (
    TagCreate,
    TagResponse,
    TaxonomyNodeCreate,
    TaxonomyNodeUpdate,
    TaxonomyNodeResponse,
    TaxonomyTreeResponse,
)
from app.services.taxonomy_service import TagService, TaxonomyService
from app.models.taxonomy import TaxonomyNode

router = APIRouter()


# Tag endpoints
@router.post("/tags", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_admin_user),
):
    """Create a new tag."""
    tag = TagService.create_tag(db, tag_data)
    return TagResponse.model_validate(tag)


@router.get("/tags", response_model=list[TagResponse])
async def list_tags(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search tag names"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """List tags with optional filtering."""
    tags = TagService.list_tags(db, category, search)
    return [TagResponse.model_validate(tag) for tag in tags]


@router.get("/tags/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Get a specific tag."""
    tag = TagService.get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return TagResponse.model_validate(tag)


@router.post("/content/{content_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_tag_to_content(
    content_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Add a tag to a content item."""
    TagService.add_tag_to_content(db, content_id, tag_id)
    return None


@router.delete("/content/{content_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_content(
    content_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Remove a tag from a content item."""
    TagService.remove_tag_from_content(db, content_id, tag_id)
    return None


# Taxonomy endpoints
@router.post("/taxonomy", response_model=TaxonomyNodeResponse, status_code=status.HTTP_201_CREATED)
async def create_taxonomy_node(
    node_data: TaxonomyNodeCreate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_admin_user),
):
    """Create a new taxonomy node."""
    node = TaxonomyService.create_node(db, node_data)
    return TaxonomyNodeResponse.model_validate(node)


@router.get("/taxonomy", response_model=list[TaxonomyTreeResponse])
async def get_taxonomy_tree(
    parent_id: Optional[int] = Query(None, description="Get children of specific parent node"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Get taxonomy tree."""
    nodes = TaxonomyService.get_tree(db, parent_id)
    
    # Build tree structure recursively
    def build_tree(node: TaxonomyNode) -> TaxonomyTreeResponse:
        children = db.query(TaxonomyNode).filter(TaxonomyNode.parent_id == node.id).all()
        return TaxonomyTreeResponse(
            id=node.id,
            name=node.name,
            slug=node.slug,
            parent_id=node.parent_id,
            level=node.level,
            metadata=node.metadata,
            children=[build_tree(child) for child in children]
        )
    
    return [build_tree(node) for node in nodes]


@router.get("/taxonomy/{node_id}", response_model=TaxonomyNodeResponse)
async def get_taxonomy_node(
    node_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Get a specific taxonomy node."""
    node = TaxonomyService.get_node(db, node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taxonomy node not found"
        )
    return TaxonomyNodeResponse.model_validate(node)


@router.put("/taxonomy/{node_id}", response_model=TaxonomyNodeResponse)
async def update_taxonomy_node(
    node_id: int,
    node_data: TaxonomyNodeUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_admin_user),
):
    """Update a taxonomy node."""
    node = TaxonomyService.update_node(db, node_id, node_data)
    return TaxonomyNodeResponse.model_validate(node)


@router.post("/content/{content_id}/taxonomy/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_taxonomy_to_content(
    content_id: int,
    node_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Add a taxonomy node to a content item."""
    TaxonomyService.add_node_to_content(db, content_id, node_id)
    return None


@router.delete("/content/{content_id}/taxonomy/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_taxonomy_from_content(
    content_id: int,
    node_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user),
):
    """Remove a taxonomy node from a content item."""
    TaxonomyService.remove_node_from_content(db, content_id, node_id)
    return None
