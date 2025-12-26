"""Tests for storage component."""

import pytest
from services.breach_monitor.storage import BreachStorage, Breach


def test_storage_initialization(temp_db):
    """Test storage initialization."""
    storage = BreachStorage(temp_db)
    assert storage.engine is not None
    assert storage.SessionLocal is not None


def test_store_breaches(temp_db):
    """Test storing breaches."""
    storage = BreachStorage(temp_db)
    
    normalized_breaches = [
        {
            "identifier": "test@example.com",
            "identifier_type": "email",
            "breach_name": "TestBreach",
            "breach_date": None,
            "data_classes": ["Email addresses"],
            "is_verified": True
        }
    ]
    
    result = storage.store_breaches(normalized_breaches)
    
    assert result["stored"] == 1
    assert result["updated"] == 0
    assert result["errors"] == 0


def test_get_breaches(temp_db):
    """Test retrieving breaches."""
    storage = BreachStorage(temp_db)
    
    # Store a breach first
    normalized_breaches = [
        {
            "identifier": "test@example.com",
            "identifier_type": "email",
            "breach_name": "TestBreach",
            "data_classes": ["Email addresses"],
            "is_verified": True
        }
    ]
    storage.store_breaches(normalized_breaches)
    
    # Retrieve breaches
    breaches = storage.get_breaches(identifier="test@example.com")
    
    assert len(breaches) == 1
    assert breaches[0].identifier == "test@example.com"
    assert breaches[0].breach_name == "TestBreach"


def test_record_check(temp_db):
    """Test recording check history."""
    storage = BreachStorage(temp_db)
    
    storage.record_check(
        identifier="test@example.com",
        identifier_type="email",
        breaches_found=2,
        new_breaches=1,
        updated_breaches=1,
        success=True
    )
    
    # Verify check was recorded (would need to query check_history table)
    # For now, just verify no exception was raised
    assert True

