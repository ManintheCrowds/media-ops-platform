"""Tests for differ component."""

import pytest
from datetime import datetime
from services.breach_monitor.differ import BreachDiffer
from services.breach_monitor.storage import Breach


def test_diff_new_breaches():
    """Test detecting new breaches."""
    differ = BreachDiffer()
    
    new_breaches = [
        {
            "identifier": "test@example.com",
            "identifier_type": "email",
            "breach_name": "NewBreach",
            "data_classes": ["Email addresses"]
        }
    ]
    
    stored_breaches = []  # No stored breaches
    
    result = differ.diff(new_breaches, stored_breaches)
    
    assert len(result["new_breaches"]) == 1
    assert len(result["updated_breaches"]) == 0
    assert len(result["unchanged_breaches"]) == 0


def test_diff_unchanged_breaches():
    """Test detecting unchanged breaches."""
    differ = BreachDiffer()
    
    new_breaches = [
        {
            "identifier": "test@example.com",
            "identifier_type": "email",
            "breach_name": "ExistingBreach",
            "data_classes": ["Email addresses"]
        }
    ]
    
    # Create mock stored breach
    stored_breach = Breach(
        identifier="test@example.com",
        identifier_type="email",
        breach_name="ExistingBreach",
        data_classes=["Email addresses"]
    )
    
    result = differ.diff(new_breaches, [stored_breach])
    
    assert len(result["new_breaches"]) == 0
    assert len(result["updated_breaches"]) == 0
    assert len(result["unchanged_breaches"]) == 1


def test_diff_updated_breaches():
    """Test detecting updated breaches."""
    differ = BreachDiffer()
    
    new_breaches = [
        {
            "identifier": "test@example.com",
            "identifier_type": "email",
            "breach_name": "UpdatedBreach",
            "data_classes": ["Email addresses", "Passwords"]  # New data class
        }
    ]
    
    stored_breach = Breach(
        identifier="test@example.com",
        identifier_type="email",
        breach_name="UpdatedBreach",
        data_classes=["Email addresses"]  # Old data classes
    )
    
    result = differ.diff(new_breaches, [stored_breach])
    
    assert len(result["new_breaches"]) == 0
    assert len(result["updated_breaches"]) == 1
    assert len(result["unchanged_breaches"]) == 0


def test_get_alertable_breaches():
    """Test getting alertable breaches."""
    differ = BreachDiffer()
    
    diff_result = {
        "new_breaches": [
            {"identifier": "test@example.com", "breach_name": "NewBreach"}
        ],
        "updated_breaches": [
            {
                "new": {
                    "identifier": "test@example.com",
                    "breach_name": "UpdatedBreach",
                    "data_classes": ["Email addresses", "Passwords"]
                },
                "old": {
                    "identifier": "test@example.com",
                    "breach_name": "UpdatedBreach",
                    "data_classes": ["Email addresses"]
                }
            }
        ],
        "unchanged_breaches": []
    }
    
    alertable = differ.get_alertable_breaches(diff_result)
    
    # Should include new breach and updated breach (with new data classes)
    assert len(alertable) == 2

