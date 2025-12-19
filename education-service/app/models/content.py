"""Content models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class ContentType(str, enum.Enum):
    """Content type enum."""
    LESSON = "lesson"
    VIDEO = "video"
    DOCUMENT = "document"
    ASSESSMENT = "assessment"
    PROJECT_TEMPLATE = "project_template"


class ContentItem(Base):
    """Content item model for educational materials."""
    
    __tablename__ = "content_items"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    content_type = Column(SQLEnum(ContentType), nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    slug = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    body = Column(Text)  # Main content
    metadata = Column(JSON)  # Content-specific data
    external_refs = Column(JSON)  # References to BookStack/Gitea/Seafile/Jellyfin
    version = Column(Integer, default=1, nullable=False)
    parent_id = Column(Integer, ForeignKey("content_items.id"), nullable=True)  # For hierarchical content
    created_by = Column(String(255), nullable=False)  # Reference to platform user
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="content_items")
    parent = relationship("ContentItem", remote_side=[id], backref="children")
    versions = relationship("ContentVersion", back_populates="content_item", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="content_tags", back_populates="content_items")
    taxonomy_nodes = relationship("TaxonomyNode", secondary="content_taxonomy", back_populates="content_items")
    progress_records = relationship("UserProgress", back_populates="content_item", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="content_item", cascade="all, delete-orphan")


class ContentVersion(Base):
    """Content version model for versioning support."""
    
    __tablename__ = "content_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    content_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    body = Column(Text)
    metadata = Column(JSON)  # Snapshot of content metadata
    created_by = Column(String(255), nullable=False)  # Reference to platform user
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    content_item = relationship("ContentItem", back_populates="versions")

