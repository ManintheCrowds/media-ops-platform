"""PII redaction utility for masking sensitive data before LLM calls."""

import re
from typing import Optional

# SSN: XXX-XX-XXXX or XXXXXXXXX
_SSN_PATTERN = re.compile(
    r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"
)

# Email: standard format
_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)

# US phone: (XXX) XXX-XXXX, XXX-XXX-XXXX, XXX.XXX.XXXX, etc.
_US_PHONE_PATTERN = re.compile(
    r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)

# International phone: +XX ... (common formats)
_INTL_PHONE_PATTERN = re.compile(
    r"\+\d{1,4}[-.\s]?(?:\d[-.\s]?){8,14}\d\b"
)

REDACTED_PLACEHOLDER = "[REDACTED]"


def redact_pii(text: Optional[str]) -> str:
    """Redact PII from text before sending to LLM.

    Masks SSN, email, and phone numbers. Use defense-in-depth:
    even for local LLMs, avoid exposing PII in prompts.

    Args:
        text: Input text that may contain PII.

    Returns:
        Text with PII replaced by [REDACTED].
    """
    if not text or not isinstance(text, str):
        return text or ""

    result = text
    result = _SSN_PATTERN.sub(REDACTED_PLACEHOLDER, result)
    result = _EMAIL_PATTERN.sub(REDACTED_PLACEHOLDER, result)
    result = _US_PHONE_PATTERN.sub(REDACTED_PLACEHOLDER, result)
    result = _INTL_PHONE_PATTERN.sub(REDACTED_PLACEHOLDER, result)

    return result
