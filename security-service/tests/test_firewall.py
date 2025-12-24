"""Tests for firewall automation."""

import pytest
from security_service.protection.firewall import FirewallAutomation
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
def firewall(db):
    """Firewall fixture."""
    return FirewallAutomation(db)


def test_create_block_rule(firewall):
    """Test creating a block rule."""
    rule = firewall.create_block_rule(
        ip_address="192.168.1.100",
        reason="Test block",
        duration_hours=1
    )
    
    assert rule is not None
    assert rule.rule_type == "ip_block"
    assert rule.target == "192.168.1.100"
    assert rule.action == "block"


def test_is_ip_blocked(firewall):
    """Test IP blocking check."""
    # Block an IP
    firewall.create_block_rule("192.168.1.200", "Test", 1)
    
    # Check if blocked
    is_blocked = firewall.is_ip_blocked("192.168.1.200")
    assert is_blocked is True
    
    # Check non-blocked IP
    is_blocked = firewall.is_ip_blocked("192.168.1.300")
    assert is_blocked is False







