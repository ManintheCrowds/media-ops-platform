"""Breach tracking models for HIBP integration."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Index
from ..base import Base


class UserBreach(Base):
    """User breach tracking model."""
    __tablename__ = "user_breaches"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # Optional - may not have user_id for email-only checks
    email = Column(String(255), nullable=False, index=True)
    breach_name = Column(String(255), nullable=False, index=True)
    breach_date = Column(DateTime, nullable=True)  # Date when breach occurred
    added_date = Column(DateTime, nullable=True)  # Date when breach was added to HIBP
    modified_date = Column(DateTime, nullable=True)  # Date when breach was last modified
    pwn_count = Column(Integer, nullable=True)  # Number of accounts affected
    description = Column(Text, nullable=True)
    data_classes = Column(JSON, nullable=True)  # List of data types exposed (Email addresses, Passwords, etc.)
    is_verified = Column(Boolean, default=True, nullable=False)
    is_fabricated = Column(Boolean, default=False, nullable=False)
    is_sensitive = Column(Boolean, default=False, nullable=False)
    is_retired = Column(Boolean, default=False, nullable=False)
    is_spam_list = Column(Boolean, default=False, nullable=False)
    is_malware = Column(Boolean, default=False, nullable=False)
    is_stealer_log = Column(Boolean, default=False, nullable=False)
    is_subscription_free = Column(Boolean, default=False, nullable=False)
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    notified = Column(Boolean, default=False, nullable=False, index=True)
    notified_at = Column(DateTime, nullable=True)
    breach_metadata = Column(JSON, nullable=True)  # Full breach data from HIBP
    
    __table_args__ = (
        Index('idx_user_breaches_email_breach', 'email', 'breach_name'),
        Index('idx_user_breaches_detected', 'detected_at', 'notified'),
        Index('idx_user_breaches_user_detected', 'user_id', 'detected_at'),
    )


class DomainBreach(Base):
    """Domain breach monitoring model."""
    __tablename__ = "domain_breaches"
    
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), nullable=False, index=True)
    breach_name = Column(String(255), nullable=False, index=True)
    breach_date = Column(DateTime, nullable=True)
    affected_emails = Column(Integer, nullable=True)  # Number of emails from this domain in breach
    affected_email_list = Column(JSON, nullable=True)  # List of affected email addresses
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    last_checked = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    notified = Column(Boolean, default=False, nullable=False, index=True)
    notified_at = Column(DateTime, nullable=True)
    breach_metadata = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_domain_breaches_domain_breach', 'domain', 'breach_name'),
        Index('idx_domain_breaches_detected', 'detected_at', 'notified'),
    )


class BreachHistory(Base):
    """Historical breach data tracking."""
    __tablename__ = "breach_history"
    
    id = Column(Integer, primary_key=True, index=True)
    breach_name = Column(String(255), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=True)
    domain = Column(String(255), nullable=True, index=True)
    breach_date = Column(DateTime, nullable=True)
    added_date = Column(DateTime, nullable=True)
    modified_date = Column(DateTime, nullable=True)
    pwn_count = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    data_classes = Column(JSON, nullable=True)
    is_verified = Column(Boolean, default=True, nullable=False)
    is_fabricated = Column(Boolean, default=False, nullable=False)
    is_sensitive = Column(Boolean, default=False, nullable=False)
    is_retired = Column(Boolean, default=False, nullable=False)
    is_spam_list = Column(Boolean, default=False, nullable=False)
    is_malware = Column(Boolean, default=False, nullable=False)
    is_stealer_log = Column(Boolean, default=False, nullable=False)
    is_subscription_free = Column(Boolean, default=False, nullable=False)
    logo_path = Column(String(500), nullable=True)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    breach_metadata = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index('idx_breach_history_domain', 'domain', 'breach_date'),
        Index('idx_breach_history_date', 'breach_date', 'is_verified'),
    )

