"""Taxonomy and tagging models."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

# Association tables for many-to-many relationships
content_tags = Table(
    "content_tags",
    Base.metadata,
    Column("content_item_id", Integer, ForeignKey("content_items.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

content_taxonomy = Table(
    "content_taxonomy",
    Base.metadata,
    Column("content_item_id", Integer, ForeignKey("content_items.id"), primary_key=True),
    Column("taxonomy_node_id", Integer, ForeignKey("taxonomy_nodes.id"), primary_key=True),
)


class Tag(Base):
    """Tag model for content tagging."""
    
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50))  # e.g., "subject", "grade_level", "skill"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    content_items = relationship("ContentItem", secondary=content_tags, back_populates="tags")


class TaxonomyNode(Base):
    """Taxonomy node model for hierarchical taxonomy."""
    
    __tablename__ = "taxonomy_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("taxonomy_nodes.id"), nullable=True)  # For hierarchical taxonomy
    level = Column(Integer, default=0, nullable=False)  # Depth in hierarchy
    metadata = Column(JSON)
    
    # Relationships
    parent = relationship("TaxonomyNode", remote_side=[id], backref="children")
    content_items = relationship("ContentItem", secondary=content_taxonomy, back_populates="taxonomy_nodes")







