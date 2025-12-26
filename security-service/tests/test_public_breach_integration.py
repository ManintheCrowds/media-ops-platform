"""Integration tests for public breach sources."""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from security_service.database import get_db, init_db
from security_service.intelligence.public_breach_sources import PublicBreachSources
from security_service.intelligence.breach_data_downloader import BreachDataDownloader
from security_service.intelligence.breach_database import BreachDatabase
from security_service.intelligence.email_breach import EmailBreachService
from security_service.intelligence.domain_breach import DomainBreachService
from security_service.config import config


@pytest.fixture
def db_session():
    """Create database session for testing."""
    init_db()
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


@pytest.mark.asyncio
async def test_breach_data_downloader_parsing():
    """Test breach data downloader parsing functions."""
    downloader = BreachDataDownloader()
    
    # Test JSON parsing
    json_data = {
        "breaches": [
            {
                "email": "test@example.com",
                "breach_name": "TestBreach",
                "breach_date": "2024-01-01",
                "data_classes": ["Email addresses"]
            }
        ]
    }
    breaches = downloader.parse_json_breach_data(json_data, "test_source")
    assert len(breaches) == 1
    assert breaches[0]["email"] == "test@example.com"
    assert breaches[0]["breach_name"] == "TestBreach"
    
    # Test CSV parsing
    csv_data = "email,breach_name,breach_date\ntest@example.com,TestBreach,2024-01-01"
    breaches = downloader.parse_csv_breach_data(csv_data, "test_source")
    assert len(breaches) == 1
    assert breaches[0]["email"] == "test@example.com"
    
    # Test text parsing
    text_data = "test1@example.com\ntest2@example.com"
    breaches = downloader.parse_text_breach_data(text_data, "test_source", "TestBreach")
    assert len(breaches) == 2
    assert all(b["breach_name"] == "TestBreach" for b in breaches)


@pytest.mark.asyncio
async def test_breach_database_import(db_session: Session):
    """Test breach database import functionality."""
    breach_db = BreachDatabase(db_session)
    
    # Create test breach data
    test_breaches = [
        {
            "email": "test@example.com",
            "breach_name": "TestBreach1",
            "breach_date": "2024-01-01",
            "data_classes": ["Email addresses"],
            "is_verified": False
        },
        {
            "email": "test2@example.com",
            "breach_name": "TestBreach1",
            "breach_date": "2024-01-01",
            "data_classes": ["Email addresses"],
            "is_verified": False
        }
    ]
    
    # Import breaches
    result = breach_db.import_breaches(test_breaches, "test_source")
    
    assert result["imported"] == 2
    assert result["errors"] == 0
    
    # Test email lookup
    breaches = breach_db.lookup_email("test@example.com")
    assert len(breaches) == 1
    assert breaches[0].email == "test@example.com"
    assert breaches[0].breach_name == "TestBreach1"
    
    # Test domain lookup
    domain_breaches = breach_db.lookup_domain("example.com")
    assert len(domain_breaches) >= 1


@pytest.mark.asyncio
async def test_public_breach_sources_lookup(db_session: Session):
    """Test public breach sources lookup functionality."""
    public_sources = PublicBreachSources(db_session)
    
    # Import test data first
    breach_db = BreachDatabase(db_session)
    test_breaches = [
        {
            "email": "lookup@test.com",
            "breach_name": "LookupTest",
            "breach_date": "2024-01-01",
            "data_classes": ["Email addresses"],
            "is_verified": False
        }
    ]
    breach_db.import_breaches(test_breaches, "test_source")
    
    # Test email lookup
    breaches = public_sources.lookup_email("lookup@test.com")
    assert len(breaches) == 1
    assert breaches[0]["email"] == "lookup@test.com"
    assert breaches[0]["breach_name"] == "LookupTest"
    
    # Test domain lookup
    domain_breaches = public_sources.lookup_domain("test.com")
    assert len(domain_breaches) >= 1


@pytest.mark.asyncio
async def test_email_breach_service_integration(db_session: Session):
    """Test email breach service with public sources."""
    # Import test data
    breach_db = BreachDatabase(db_session)
    test_breaches = [
        {
            "email": "service@test.com",
            "breach_name": "ServiceTest",
            "breach_date": "2024-01-01",
            "data_classes": ["Email addresses"],
            "is_verified": False
        }
    ]
    breach_db.import_breaches(test_breaches, "test_source")
    
    # Test email breach service
    email_service = EmailBreachService(db_session)
    breaches = await email_service.check_email("service@test.com")
    
    assert len(breaches) >= 1
    assert any(b["breach_name"] == "ServiceTest" for b in breaches)


@pytest.mark.asyncio
async def test_domain_breach_service_integration(db_session: Session):
    """Test domain breach service with public sources."""
    # Import test data
    breach_db = BreachDatabase(db_session)
    test_breaches = [
        {
            "email": "user1@domain-test.com",
            "breach_name": "DomainTest",
            "breach_date": "2024-01-01",
            "data_classes": ["Email addresses"],
            "is_verified": False
        },
        {
            "email": "user2@domain-test.com",
            "breach_name": "DomainTest",
            "breach_date": "2024-01-01",
            "data_classes": ["Email addresses"],
            "is_verified": False
        }
    ]
    breach_db.import_breaches(test_breaches, "test_source")
    
    # Test domain breach service
    domain_service = DomainBreachService(db_session)
    breaches = await domain_service.check_domain("domain-test.com")
    
    assert len(breaches) >= 1


@pytest.mark.asyncio
async def test_breach_database_statistics(db_session: Session):
    """Test breach database statistics."""
    breach_db = BreachDatabase(db_session)
    
    # Import test data
    test_breaches = [
        {
            "email": f"user{i}@stats-test.com",
            "breach_name": "StatsTest",
            "breach_date": "2024-01-01",
            "data_classes": ["Email addresses"],
            "is_verified": False
        }
        for i in range(5)
    ]
    breach_db.import_breaches(test_breaches, "test_source")
    
    # Get statistics
    stats = breach_db.get_breach_statistics()
    
    assert stats["total_breach_records"] >= 5
    assert stats["unique_emails"] >= 5
    assert stats["unique_breach_names"] >= 1


@pytest.mark.asyncio
async def test_public_sources_statistics(db_session: Session):
    """Test public breach sources statistics."""
    public_sources = PublicBreachSources(db_session)
    
    # Import test data
    breach_db = BreachDatabase(db_session)
    test_breaches = [
        {
            "email": f"user{i}@stats-test.com",
            "breach_name": "StatsTest",
            "breach_date": "2024-01-01",
            "data_classes": ["Email addresses"],
            "is_verified": False
        }
        for i in range(3)
    ]
    breach_db.import_breaches(test_breaches, "test_source")
    
    # Get statistics
    stats = public_sources.get_statistics()
    
    assert "total_breach_records" in stats
    assert "unique_emails" in stats
    assert "unique_breach_names" in stats
    assert "unique_domains" in stats
    assert "last_updated" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

