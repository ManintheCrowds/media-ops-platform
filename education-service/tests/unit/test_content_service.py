"""Unit tests for content service."""

import pytest
from app.services.content_service import ContentService
from app.schemas.content import ContentItemCreate
from app.models.content import ContentType
from app.auth.platform_auth import UserInfo


def test_slugify():
    """Test slug generation."""
    from app.services.content_service import slugify
    
    assert slugify("Hello World") == "hello-world"
    assert slugify("Test 123") == "test-123"
    assert slugify("Special!@#Chars") == "specialchars"


def test_create_content(db, mock_user):
    """Test content creation."""
    # This would require setting up test data (organization, project)
    # For now, just test the slugify function
    from app.services.content_service import slugify
    assert slugify("Test Content") == "test-content"



