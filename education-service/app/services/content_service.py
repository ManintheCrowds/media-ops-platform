"""Content service for business logic."""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import HTTPException, status
from app.models.content import ContentItem, ContentVersion, ContentType
from app.models.project import Project
from app.schemas.content import ContentItemCreate, ContentItemUpdate
from app.auth.platform_auth import UserInfo
import re


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


class ContentService:
    """Service for content management operations."""
    
    @staticmethod
    def create_content(
        db: Session,
        content_data: ContentItemCreate,
        user: UserInfo
    ) -> ContentItem:
        """Create a new content item."""
        # Verify project exists
        project = db.query(Project).filter(Project.id == content_data.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Generate slug if not provided
        slug = content_data.slug or slugify(content_data.title)
        
        # Check if slug is unique within project
        existing = db.query(ContentItem).filter(
            ContentItem.project_id == content_data.project_id,
            ContentItem.slug == slug
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content with this slug already exists in project"
            )
        
        # Create content item
        content = ContentItem(
            project_id=content_data.project_id,
            title=content_data.title,
            slug=slug,
            description=content_data.description,
            body=content_data.body,
            content_type=content_data.content_type,
            metadata=content_data.metadata or {},
            external_refs=content_data.external_refs or {},
            parent_id=content_data.parent_id,
            version=1,
            created_by=user.sub
        )
        
        db.add(content)
        db.commit()
        db.refresh(content)
        
        # Create initial version
        ContentService._create_version(db, content, user)
        
        return content
    
    @staticmethod
    def get_content(db: Session, content_id: int) -> Optional[ContentItem]:
        """Get content item by ID."""
        return db.query(ContentItem).filter(ContentItem.id == content_id).first()
    
    @staticmethod
    def list_content(
        db: Session,
        project_id: Optional[int] = None,
        content_type: Optional[ContentType] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[ContentItem], int]:
        """List content items with filtering and pagination."""
        query = db.query(ContentItem)
        
        if project_id:
            query = query.filter(ContentItem.project_id == project_id)
        
        if content_type:
            query = query.filter(ContentItem.content_type == content_type)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    ContentItem.title.ilike(search_term),
                    ContentItem.description.ilike(search_term),
                    ContentItem.body.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        items = query.order_by(ContentItem.created_at.desc()).offset(offset).limit(page_size).all()
        
        return items, total
    
    @staticmethod
    def update_content(
        db: Session,
        content_id: int,
        content_data: ContentItemUpdate,
        user: UserInfo
    ) -> ContentItem:
        """Update content item."""
        content = ContentService.get_content(db, content_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        # Update fields
        if content_data.title is not None:
            content.title = content_data.title
            # Update slug if title changed
            content.slug = slugify(content_data.title)
        
        if content_data.description is not None:
            content.description = content_data.description
        
        if content_data.body is not None:
            content.body = content_data.body
        
        if content_data.metadata is not None:
            content.metadata = content_data.metadata
        
        if content_data.external_refs is not None:
            content.external_refs = content_data.external_refs
        
        if content_data.parent_id is not None:
            content.parent_id = content_data.parent_id
        
        # Increment version
        content.version += 1
        
        db.commit()
        db.refresh(content)
        
        # Create new version
        ContentService._create_version(db, content, user)
        
        return content
    
    @staticmethod
    def delete_content(db: Session, content_id: int) -> bool:
        """Delete content item."""
        content = ContentService.get_content(db, content_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        db.delete(content)
        db.commit()
        return True
    
    @staticmethod
    def get_versions(db: Session, content_id: int) -> List[ContentVersion]:
        """Get all versions of a content item."""
        return db.query(ContentVersion).filter(
            ContentVersion.content_item_id == content_id
        ).order_by(ContentVersion.version_number.desc()).all()
    
    @staticmethod
    def get_version(db: Session, content_id: int, version_number: int) -> Optional[ContentVersion]:
        """Get specific version of content item."""
        return db.query(ContentVersion).filter(
            ContentVersion.content_item_id == content_id,
            ContentVersion.version_number == version_number
        ).first()
    
    @staticmethod
    def revert_to_version(
        db: Session,
        content_id: int,
        version_number: int,
        user: UserInfo
    ) -> ContentItem:
        """Revert content item to a specific version."""
        content = ContentService.get_content(db, content_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found"
            )
        
        version = ContentService.get_version(db, content_id, version_number)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        # Restore version data
        content.title = version.title
        content.body = version.body
        content.metadata = version.metadata
        content.version += 1
        
        db.commit()
        db.refresh(content)
        
        # Create new version after revert
        ContentService._create_version(db, content, user)
        
        return content
    
    @staticmethod
    def _create_version(db: Session, content: ContentItem, user: UserInfo) -> ContentVersion:
        """Create a version snapshot of content."""
        version = ContentVersion(
            content_item_id=content.id,
            version_number=content.version,
            title=content.title,
            body=content.body,
            metadata=content.metadata or {},
            created_by=user.sub
        )
        db.add(version)
        db.commit()
        return version

