"""Shared SQLAlchemy Base for all models."""

from sqlalchemy.ext.declarative import declarative_base

# Single Base instance shared by all models
Base = declarative_base()

