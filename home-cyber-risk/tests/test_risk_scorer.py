"""Tests for risk scorer component."""

import pytest
from datetime import datetime, timezone, timedelta
from services.breach_monitor.risk_scorer import RiskScorer


def test_calculate_risk_score_password_breach():
    """Test risk score for password breach."""
    scorer = RiskScorer()
    
    breach = {
        "data_classes": ["Passwords", "Email addresses"],
        "breach_date": datetime.now(timezone.utc) - timedelta(days=10),
        "is_verified": True,
        "pwn_count": 1000000
    }
    
    score = scorer.calculate_risk_score(breach)
    assert score >= 80  # Should be critical
    assert score <= 100


def test_calculate_risk_score_old_breach():
    """Test risk score for old breach."""
    scorer = RiskScorer()
    
    breach = {
        "data_classes": ["Email addresses"],
        "breach_date": datetime.now(timezone.utc) - timedelta(days=1000),
        "is_verified": True,
        "pwn_count": 1000
    }
    
    score = scorer.calculate_risk_score(breach)
    assert score < 80  # Should be lower than critical


def test_classify_priority():
    """Test priority classification."""
    scorer = RiskScorer()
    
    assert scorer.classify_priority(85) == "Critical"
    assert scorer.classify_priority(70) == "High"
    assert scorer.classify_priority(50) == "Medium"
    assert scorer.classify_priority(30) == "Low"


def test_assess_impact_password():
    """Test impact assessment for password breach."""
    scorer = RiskScorer()
    
    breach = {
        "data_classes": ["Passwords", "Email addresses"]
    }
    
    impact = scorer.assess_impact(breach)
    assert impact["severity"] == "High"
    assert impact["requires_password_change"] is True
    assert impact["requires_2fa"] is True
    assert "Passwords" in impact["exposed_data_types"]


def test_score_breach():
    """Test complete breach scoring."""
    scorer = RiskScorer()
    
    breach = {
        "data_classes": ["Passwords"],
        "breach_date": datetime.now(timezone.utc) - timedelta(days=5),
        "is_verified": True,
        "pwn_count": 500000
    }
    
    scored = scorer.score_breach(breach)
    assert "risk_score" in scored
    assert "priority" in scored
    assert "impact" in scored
    assert scored["risk_score"] > 0
    assert scored["priority"] in ["Critical", "High", "Medium", "Low"]

