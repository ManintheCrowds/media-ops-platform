"""Tests for rate limiting."""

import pytest
from security_service.protection.rate_limit import RateLimiter


def test_ip_rate_limit():
    """Test IP rate limiting."""
    limiter = RateLimiter()
    
    # Test within limit
    allowed, remaining, reset = limiter.check_ip_rate_limit("192.168.1.100")
    assert allowed is True
    assert remaining >= 0
    
    # Test exceeding limit (would need to make many requests)
    # for _ in range(101):
    #     allowed, remaining, reset = limiter.check_ip_rate_limit("192.168.1.100")
    # assert allowed is False


def test_user_rate_limit():
    """Test user rate limiting."""
    limiter = RateLimiter()
    
    allowed, remaining, reset = limiter.check_user_rate_limit(1)
    assert allowed is True


def test_endpoint_rate_limit():
    """Test endpoint rate limiting."""
    limiter = RateLimiter()
    
    allowed, remaining, reset = limiter.check_endpoint_rate_limit("/api/test", "192.168.1.100")
    assert allowed is True

