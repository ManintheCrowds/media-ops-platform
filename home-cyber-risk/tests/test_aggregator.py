"""Tests for aggregator component."""

import pytest
from services.breach_monitor.aggregator import BreachAggregator


def test_aggregate_results():
    """Test aggregating results from multiple sources."""
    aggregator = BreachAggregator()
    
    source_results = {
        "hibp": [
            {
                "identifier": "test@example.com",
                "breach_name": "TestBreach",
                "data_classes": ["Email addresses"],
                "source": "hibp"
            }
        ],
        "public_db": [
            {
                "identifier": "test@example.com",
                "breach_name": "TestBreach",
                "data_classes": ["Email addresses", "Passwords"],
                "source": "public_db"
            }
        ]
    }
    
    aggregated = aggregator.aggregate_results(source_results)
    
    assert len(aggregated) == 1
    assert aggregated[0]["breach_name"] == "TestBreach"
    assert "hibp" in aggregated[0]["_sources"]
    assert "public_db" in aggregated[0]["_sources"]
    # Data classes should be merged
    assert "Email addresses" in aggregated[0]["data_classes"]
    assert "Passwords" in aggregated[0]["data_classes"]


def test_deduplicate_breaches():
    """Test breach deduplication."""
    aggregator = BreachAggregator()
    
    breaches = [
        {"identifier": "test@example.com", "breach_name": "Breach1"},
        {"identifier": "test@example.com", "breach_name": "Breach1"},  # Duplicate
        {"identifier": "test@example.com", "breach_name": "Breach2"},
    ]
    
    deduplicated = aggregator.deduplicate_breaches(breaches)
    
    assert len(deduplicated) == 2


def test_calculate_confidence():
    """Test confidence calculation."""
    aggregator = BreachAggregator()
    
    assert aggregator.calculate_confidence(0) == 0.0
    assert aggregator.calculate_confidence(1) == 0.6
    assert aggregator.calculate_confidence(2) == 0.8
    assert aggregator.calculate_confidence(3) == 1.0
    assert aggregator.calculate_confidence(5) == 1.0

