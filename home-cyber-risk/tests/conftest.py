"""Pytest configuration and fixtures."""

import pytest
import tempfile
import os
from pathlib import Path

@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield f"sqlite:///{db_path}"
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture
def sample_identifiers():
    """Sample identifiers for testing."""
    return {
        "emails": ["test@example.com"],
        "usernames": ["testuser"],
        "domains": ["example.com"],
        "metadata": {}
    }

@pytest.fixture
def sample_breach_data():
    """Sample breach data from HIBP API."""
    return [
        {
            "Name": "TestBreach",
            "Title": "Test Breach",
            "Domain": "example.com",
            "BreachDate": "2024-01-01",
            "AddedDate": "2024-01-15",
            "ModifiedDate": "2024-01-15",
            "PwnCount": 1000000,
            "Description": "A test data breach",
            "DataClasses": ["Email addresses", "Passwords"],
            "IsVerified": True,
            "IsFabricated": False,
            "IsSensitive": False,
            "IsRetired": False,
            "IsSpamList": False
        }
    ]

