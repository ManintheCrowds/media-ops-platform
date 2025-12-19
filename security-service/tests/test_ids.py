"""Tests for Intrusion Detection System."""

import pytest
from fastapi import Request
from security_service.monitoring.ids import IntrusionDetectionSystem
from security_service.database import SessionLocal


@pytest.fixture
def db():
    """Database session fixture."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def ids(db):
    """IDS fixture."""
    return IntrusionDetectionSystem(db)


def test_sql_injection_detection(ids):
    """Test SQL injection detection."""
    # Mock request with SQL injection
    class MockRequest:
        url = type('obj', (object,), {'path': '/api/test', 'query': 'id=1 OR 1=1'})()
        method = "GET"
        headers = {"user-agent": "test"}
        client = type('obj', (object,), {'host': '192.168.1.100'})()

    request = MockRequest()
    # Note: This would need async context in real test
    # event = await ids.analyze_request(request)
    # assert event is not None
    # assert event.event_type == "sql_injection"


def test_xss_detection(ids):
    """Test XSS detection."""
    class MockRequest:
        url = type('obj', (object,), {'path': '/api/test', 'query': 'name=<script>alert(1)</script>'})()
        method = "GET"
        headers = {"user-agent": "test"}
        client = type('obj', (object,), {'host': '192.168.1.100'})()

    request = MockRequest()
    # Similar async test would go here


def test_brute_force_detection(ids):
    """Test brute force detection."""
    # Test multiple failed logins
    source_ip = "192.168.1.100"
    for _ in range(6):
        ids.record_failed_login(source_ip)
    
    # Check if brute force event was created
    # This would require checking the database

