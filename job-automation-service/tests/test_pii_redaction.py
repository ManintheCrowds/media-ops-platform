"""Tests for PII redaction utility."""

import pytest
from app.utils.pii_redaction import redact_pii


def test_redact_email():
    """Test email redaction."""
    text = "Contact me at john.doe@example.com for details."
    assert "[REDACTED]" in redact_pii(text)
    assert "john.doe@example.com" not in redact_pii(text)


def test_redact_ssn():
    """Test SSN redaction."""
    text = "SSN: 123-45-6789"
    assert "[REDACTED]" in redact_pii(text)
    assert "123-45-6789" not in redact_pii(text)


def test_redact_phone():
    """Test US phone redaction."""
    text = "Call (555) 123-4567 for details."
    result = redact_pii(text)
    assert "[REDACTED]" in result
    assert "123-4567" not in result


def test_redact_empty():
    """Test empty input."""
    assert redact_pii("") == ""
    assert redact_pii(None) == ""


def test_redact_no_pii():
    """Test text with no PII passes through."""
    text = "Python developer with FastAPI experience."
    assert redact_pii(text) == text
