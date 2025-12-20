"""Project service for business logic."""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from app.models.project import Project, ProjectStatus
from app.models.organization import Organization
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.auth.platform_auth import UserInfo
import re


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


class ProjectService:
    """Service for project management operations."""
    
    @staticmethod
    def create_project(
        db: Session,
        project_data: ProjectCreate,
        user: UserInfo
    ) -> Project:
        """Create a new project."""
        # Verify organization exists
        org = db.query(Organization).filter(Organization.id == project_data.organization_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Generate slug if not provided
        slug = project_data.slug or slugify(project_data.name)
        
        # Check if slug is unique within organization
        existing = db.query(Project).filter(
            Project.organization_id == project_data.organization_id,
            Project.slug == slug
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project with this slug already exists in organization"
            )
        
        # Create project
        project = Project(
            organization_id=project_data.organization_id,
            name=project_data.name,
            slug=slug,
            description=project_data.description,
            status=project_data.status,
            metadata=project_data.metadata or {},
            created_by=user.sub
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        return project
    
    @staticmethod
    def get_project(db: Session, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        return db.query(Project).filter(Project.id == project_id).first()
    
    @staticmethod
    def list_projects(
        db: Session,
        organization_id: Optional[int] = None,
        status: Optional[ProjectStatus] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Project], int]:
        """List projects with filtering and pagination."""
        query = db.query(Project)
        
        if organization_id:
            query = query.filter(Project.organization_id == organization_id)
        
        if status:
            query = query.filter(Project.status == status)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Project.name.ilike(search_term),
                    Project.description.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        items = query.order_by(Project.created_at.desc()).offset(offset).limit(page_size).all()
        
        return items, total
    
    @staticmethod
    def update_project(
        db: Session,
        project_id: int,
        project_data: ProjectUpdate,
        user: UserInfo
    ) -> Project:
        """Update project."""
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Update fields
        if project_data.name is not None:
            project.name = project_data.name
            # Update slug if name changed
            if not project_data.slug:
                project.slug = slugify(project_data.name)
        
        if project_data.slug is not None:
            project.slug = project_data.slug
        
        if project_data.description is not None:
            project.description = project_data.description
        
        if project_data.status is not None:
            project.status = project_data.status
        
        if project_data.metadata is not None:
            project.metadata = project_data.metadata
        
        db.commit()
        db.refresh(project)
        
        return project
    
    @staticmethod
    def delete_project(db: Session, project_id: int) -> bool:
        """Delete project."""
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        db.delete(project)
        db.commit()
        return True
    
    @staticmethod
    def get_project_content(
        db: Session,
        project_id: int
    ) -> List:
        """Get all content items in a project."""
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return project.content_items


