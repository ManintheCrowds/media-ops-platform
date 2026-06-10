"""Data models for the platform."""

import logging
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from datetime import datetime
from app.auth.encryption import encrypt_token, decrypt_token, is_encrypted, EncryptionError
from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Service(Base):
    """Service registry model."""
    
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    service_type = Column(String(50), nullable=False)  # file_storage, media_server, etc.
    base_url = Column(String(255), nullable=False)
    api_url = Column(String(255))
    health_check_url = Column(String(255))
    is_active = Column(Boolean, default=True)
    requires_auth = Column(Boolean, default=True)
    _auth_token_encrypted = Column('auth_token', Text)  # Encrypted token storage in database
    service_metadata = Column(Text)  # JSON metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_health_check = Column(DateTime(timezone=True))
    health_status = Column(String(20), default="unknown")  # healthy, unhealthy, unknown
    
    @hybrid_property
    def auth_token(self):
        """Get decrypted auth token."""
        if not hasattr(self, "_sa_instance_state"):
            return None

        encrypted = self._auth_token_encrypted
        if encrypted is None:
            return None
        if not isinstance(encrypted, str):
            return None

        # Migration: if not encrypted, encrypt it on first access
        if not is_encrypted(encrypted):
            try:
                logger.info(
                    "Migrating plain-text token for service %s to encrypted format",
                    self.id,
                )
                self._auth_token_encrypted = encrypt_token(
                    encrypted,
                    settings.secret_key,
                )
            except Exception as e:
                logger.error(f"Failed to encrypt token during migration: {e}")
                return encrypted

        try:
            return decrypt_token(self._auth_token_encrypted, settings.secret_key)
        except EncryptionError as e:
            logger.error(f"Failed to decrypt token for service {self.id}: {e}")
            return None
    
    @auth_token.setter
    def auth_token(self, value):
        """Set encrypted auth token."""
        if value is None:
            self._auth_token_encrypted = None
        else:
            try:
                self._auth_token_encrypted = encrypt_token(value, settings.secret_key)
            except EncryptionError as e:
                logger.error(f"Failed to encrypt token: {e}")
                raise


