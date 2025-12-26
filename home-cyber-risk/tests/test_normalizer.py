"""Tests for normalizer component."""

import pytest
from services.breach_monitor.normalizer import BreachNormalizer


def test_normalize_single_breach(sample_breach_data):
    """Test normalizing a single breach."""
    normalizer = BreachNormalizer()
    
    normalized = normalizer._normalize_single(
        sample_breach_data[0],
        "test@example.com",
        "email"
    )
    
    assert normalized["identifier"] == "test@example.com"
    assert normalized["identifier_type"] == "email"
    assert normalized["breach_name"] == "TestBreach"
    assert normalized["data_classes"] == ["Email addresses", "Passwords"]
    assert normalized["is_verified"] is True


def test_normalize_deduplication():
    """Test deduplication in normalization."""
    normalizer = BreachNormalizer()
    
    raw_breaches = [
        {"Name": "TestBreach", "BreachDate": "2024-01-01"},
        {"Name": "TestBreach", "BreachDate": "2024-01-01"},  # Duplicate
        {"Name": "AnotherBreach", "BreachDate": "2024-01-02"}
    ]
    
    normalized = normalizer.normalize(raw_breaches, "test@example.com", "email")
    
    # Should have 2 unique breaches
    assert len(normalized) == 2
    assert len([b for b in normalized if b["breach_name"] == "TestBreach"]) == 1


def test_validate_normalized_breach():
    """Test validation of normalized breach."""
    normalizer = BreachNormalizer()
    
    valid_breach = {
        "identifier": "test@example.com",
        "identifier_type": "email",
        "breach_name": "TestBreach"
    }
    
    assert normalizer.validate(valid_breach) is True
    
    invalid_breach = {
        "identifier": "test@example.com"
        # Missing required fields
    }
    
    assert normalizer.validate(invalid_breach) is False

