"""Database models for the educational service."""

from app.database import Base

# Import all models so they're registered with Base
from app.models.organization import Organization
from app.models.project import Project
from app.models.content import ContentItem, ContentVersion
from app.models.taxonomy import TaxonomyNode, Tag, ContentTag, ContentTaxonomy
from app.models.progress import UserProgress
from app.models.assessment import Assessment, AssessmentSubmission
from app.models.pi_device import PiDevice, PiSyncPackage

__all__ = [
    "Base",
    "Organization",
    "Project",
    "ContentItem",
    "ContentVersion",
    "TaxonomyNode",
    "Tag",
    "ContentTag",
    "ContentTaxonomy",
    "UserProgress",
    "Assessment",
    "AssessmentSubmission",
    "PiDevice",
    "PiSyncPackage",
]




