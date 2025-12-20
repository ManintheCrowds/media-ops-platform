"""Taxonomy and tagging service."""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from app.models.taxonomy import Tag, TaxonomyNode
from app.models.content import ContentItem
from app.schemas.taxonomy import TagCreate, TaxonomyNodeCreate, TaxonomyNodeUpdate
from app.auth.platform_auth import UserInfo
import re


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def calculate_taxonomy_level(node: TaxonomyNode, db: Session) -> int:
    """Calculate the level/depth of a taxonomy node."""
    if node.parent_id is None:
        return 0
    
    parent = db.query(TaxonomyNode).filter(TaxonomyNode.id == node.parent_id).first()
    if parent:
        return parent.level + 1
    return 0


class TagService:
    """Service for tag operations."""
    
    @staticmethod
    def create_tag(db: Session, tag_data: TagCreate) -> Tag:
        """Create a new tag."""
        # Check if tag already exists
        existing = db.query(Tag).filter(Tag.name == tag_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag with this name already exists"
            )
        
        tag = Tag(name=tag_data.name, category=tag_data.category)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag
    
    @staticmethod
    def get_tag(db: Session, tag_id: int) -> Optional[Tag]:
        """Get tag by ID."""
        return db.query(Tag).filter(Tag.id == tag_id).first()
    
    @staticmethod
    def list_tags(
        db: Session,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Tag]:
        """List tags with optional filtering."""
        query = db.query(Tag)
        
        if category:
            query = query.filter(Tag.category == category)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(Tag.name.ilike(search_term))
        
        return query.order_by(Tag.name).all()
    
    @staticmethod
    def add_tag_to_content(db: Session, content_id: int, tag_id: int) -> bool:
        """Add a tag to a content item."""
        content = db.query(ContentItem).filter(ContentItem.id == content_id).first()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        tag = TagService.get_tag(db, tag_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )
        
        if tag not in content.tags:
            content.tags.append(tag)
            db.commit()
        
        return True
    
    @staticmethod
    def remove_tag_from_content(db: Session, content_id: int, tag_id: int) -> bool:
        """Remove a tag from a content item."""
        content = db.query(ContentItem).filter(ContentItem.id == content_id).first()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        tag = TagService.get_tag(db, tag_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )
        
        if tag in content.tags:
            content.tags.remove(tag)
            db.commit()
        
        return True


class TaxonomyService:
    """Service for taxonomy operations."""
    
    @staticmethod
    def create_node(db: Session, node_data: TaxonomyNodeCreate) -> TaxonomyNode:
        """Create a new taxonomy node."""
        # Generate slug if not provided
        slug = node_data.slug or slugify(node_data.name)
        
        # Check if slug is unique
        existing = db.query(TaxonomyNode).filter(TaxonomyNode.slug == slug).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Taxonomy node with this slug already exists"
            )
        
        # Create node
        node = TaxonomyNode(
            name=node_data.name,
            slug=slug,
            parent_id=node_data.parent_id,
            metadata=node_data.metadata or {},
            level=0  # Will be calculated
        )
        
        db.add(node)
        db.flush()  # Flush to get ID
        
        # Calculate and set level
        node.level = calculate_taxonomy_level(node, db)
        db.commit()
        db.refresh(node)
        
        return node
    
    @staticmethod
    def get_node(db: Session, node_id: int) -> Optional[TaxonomyNode]:
        """Get taxonomy node by ID."""
        return db.query(TaxonomyNode).filter(TaxonomyNode.id == node_id).first()
    
    @staticmethod
    def get_tree(db: Session, parent_id: Optional[int] = None) -> List[TaxonomyNode]:
        """Get taxonomy tree starting from a parent node."""
        query = db.query(TaxonomyNode)
        
        if parent_id is None:
            query = query.filter(TaxonomyNode.parent_id.is_(None))
        else:
            query = query.filter(TaxonomyNode.parent_id == parent_id)
        
        return query.order_by(TaxonomyNode.name).all()
    
    @staticmethod
    def update_node(
        db: Session,
        node_id: int,
        node_data: TaxonomyNodeUpdate
    ) -> TaxonomyNode:
        """Update a taxonomy node."""
        node = TaxonomyService.get_node(db, node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Taxonomy node not found"
            )
        
        if node_data.name is not None:
            node.name = node_data.name
            if not node_data.slug:
                node.slug = slugify(node_data.name)
        
        if node_data.slug is not None:
            node.slug = node_data.slug
        
        if node_data.metadata is not None:
            node.metadata = node_data.metadata
        
        if node_data.parent_id is not None:
            # Prevent circular references
            if node_data.parent_id == node_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot set parent to self"
                )
            
            # Check if parent is a descendant (would create cycle)
            parent = TaxonomyService.get_node(db, node_data.parent_id)
            if parent:
                # Check if node is ancestor of parent
                current = parent
                while current.parent_id:
                    if current.parent_id == node_id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot create circular reference"
                        )
                    current = TaxonomyService.get_node(db, current.parent_id)
            
            node.parent_id = node_data.parent_id
            node.level = calculate_taxonomy_level(node, db)
        
        db.commit()
        db.refresh(node)
        return node
    
    @staticmethod
    def add_node_to_content(db: Session, content_id: int, node_id: int) -> bool:
        """Add a taxonomy node to a content item."""
        content = db.query(ContentItem).filter(ContentItem.id == content_id).first()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        node = TaxonomyService.get_node(db, node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Taxonomy node not found"
            )
        
        if node not in content.taxonomy_nodes:
            content.taxonomy_nodes.append(node)
            db.commit()
        
        return True
    
    @staticmethod
    def remove_node_from_content(db: Session, content_id: int, node_id: int) -> bool:
        """Remove a taxonomy node from a content item."""
        content = db.query(ContentItem).filter(ContentItem.id == content_id).first()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        node = TaxonomyService.get_node(db, node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Taxonomy node not found"
            )
        
        if node in content.taxonomy_nodes:
            content.taxonomy_nodes.remove(node)
            db.commit()
        
        return True


