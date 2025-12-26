"""Storage component for persisting breach data."""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean, Index, Text, Float
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.exc import SQLAlchemyError
import os

logger = logging.getLogger(__name__)

Base = declarative_base()


class Breach(Base):
    """Breach record model."""
    __tablename__ = "breaches"
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(255), nullable=False, index=True)
    identifier_type = Column(String(50), nullable=False, index=True)
    breach_name = Column(String(255), nullable=False, index=True)
    breach_date = Column(DateTime, nullable=True)
    data_classes = Column(JSON, nullable=True)
    pwn_count = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=True, nullable=False)
    domain = Column(String(255), nullable=True)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    notified = Column(Boolean, default=False, nullable=False, index=True)
    raw_data = Column(JSON, nullable=True)
    # New fields for multi-source and risk scoring
    risk_score = Column(Integer, nullable=True, index=True)
    priority = Column(String(20), nullable=True, index=True)
    source = Column(String(50), nullable=False, index=True, default="unknown")
    sources = Column(JSON, nullable=True)  # Multiple sources confirming
    confidence = Column(Float, nullable=True)
    
    __table_args__ = (
        Index('idx_breaches_identifier_breach', 'identifier', 'breach_name'),
        Index('idx_breaches_first_seen', 'first_seen'),
        Index('idx_breaches_notified', 'notified'),
        Index('idx_breaches_risk_score', 'risk_score'),
        Index('idx_breaches_priority', 'priority'),
        Index('idx_breaches_source', 'source'),
    )


class CheckHistory(Base):
    """Check history tracking."""
    __tablename__ = "check_history"
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(255), nullable=False, index=True)
    identifier_type = Column(String(50), nullable=False)
    check_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    breaches_found = Column(Integer, default=0, nullable=False)
    new_breaches = Column(Integer, default=0, nullable=False)
    updated_breaches = Column(Integer, default=0, nullable=False)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(String(500), nullable=True)


class BreachStorage:
    """Handles storage and retrieval of breach data."""
    
    def __init__(self, database_url: str):
        """
        Initialize storage.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        # Ensure data directory exists for SQLite
        if "sqlite" in self.database_url:
            db_path = self.database_url.replace("sqlite:///", "")
            if "/" in db_path or "\\" in db_path:
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        Base.metadata.create_all(bind=self.engine)
        
        # Migrate existing database if needed (add new columns)
        if "sqlite" in self.database_url:
            self._migrate_schema()
        
        logger.info("Database initialized")
    
    def _migrate_schema(self):
        """Migrate existing database schema to add new columns."""
        from sqlalchemy import inspect, text
        
        inspector = inspect(self.engine)
        
        # Check if breaches table exists
        if "breaches" not in inspector.get_table_names():
            return
        
        # Get existing columns
        existing_columns = [col["name"] for col in inspector.get_columns("breaches")]
        
        # Columns to add if missing
        new_columns = {
            "risk_score": "INTEGER",
            "priority": "VARCHAR(20)",
            "source": "VARCHAR(50) NOT NULL DEFAULT 'unknown'",
            "sources": "JSON",
            "confidence": "REAL"
        }
        
        # Add missing columns
        with self.engine.connect() as conn:
            for col_name, col_type in new_columns.items():
                if col_name not in existing_columns:
                    try:
                        if col_name == "source":
                            # Source needs a default value
                            conn.execute(text(f"ALTER TABLE breaches ADD COLUMN {col_name} {col_type}"))
                            # Update existing rows with default
                            conn.execute(text("UPDATE breaches SET source = 'unknown' WHERE source IS NULL"))
                        else:
                            conn.execute(text(f"ALTER TABLE breaches ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                        logger.info(f"Added column {col_name} to breaches table")
                    except Exception as e:
                        logger.warning(f"Could not add column {col_name}: {e}")
                        conn.rollback()
    
    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()
    
    def store_breaches(self, normalized_breaches: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Store normalized breaches in database.
        
        Args:
            normalized_breaches: List of normalized breach dictionaries
        
        Returns:
            Dictionary with counts: stored, updated, errors
        """
        session = self.get_session()
        stored = 0
        updated = 0
        errors = 0
        
        try:
            for breach_data in normalized_breaches:
                try:
                    # Check if breach already exists
                    existing = session.query(Breach).filter(
                        Breach.identifier == breach_data["identifier"],
                        Breach.breach_name == breach_data["breach_name"]
                    ).first()
                    
                    if existing:
                        # Update existing breach
                        existing.last_seen = datetime.now(timezone.utc)
                        existing.breach_date = breach_data.get("breach_date") or existing.breach_date
                        existing.data_classes = breach_data.get("data_classes") or existing.data_classes
                        existing.pwn_count = breach_data.get("pwn_count") or existing.pwn_count
                        existing.description = breach_data.get("description") or existing.description
                        existing.is_verified = breach_data.get("is_verified", existing.is_verified)
                        existing.domain = breach_data.get("domain") or existing.domain
                        existing.raw_data = breach_data.get("raw_data") or existing.raw_data
                        # Update new fields
                        existing.risk_score = breach_data.get("risk_score") or existing.risk_score
                        existing.priority = breach_data.get("priority") or existing.priority
                        existing.source = breach_data.get("source") or existing.source
                        existing.sources = breach_data.get("sources") or existing.sources
                        existing.confidence = breach_data.get("confidence") or existing.confidence
                        updated += 1
                    else:
                        # Create new breach
                        new_breach = Breach(
                            identifier=breach_data["identifier"],
                            identifier_type=breach_data["identifier_type"],
                            breach_name=breach_data["breach_name"],
                            breach_date=breach_data.get("breach_date"),
                            data_classes=breach_data.get("data_classes"),
                            pwn_count=breach_data.get("pwn_count"),
                            description=breach_data.get("description"),
                            is_verified=breach_data.get("is_verified", True),
                            domain=breach_data.get("domain"),
                            raw_data=breach_data.get("raw_data"),
                            risk_score=breach_data.get("risk_score"),
                            priority=breach_data.get("priority"),
                            source=breach_data.get("source", "unknown"),
                            sources=breach_data.get("sources"),
                            confidence=breach_data.get("confidence")
                        )
                        session.add(new_breach)
                        stored += 1
                        
                except Exception as e:
                    logger.error(f"Error storing breach: {e}")
                    errors += 1
                    continue
            
            session.commit()
            logger.info(f"Stored {stored} new breaches, updated {updated} existing, {errors} errors")
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error storing breaches: {e}")
            errors += len(normalized_breaches)
        finally:
            session.close()
        
        return {
            "stored": stored,
            "updated": updated,
            "errors": errors
        }
    
    def get_breaches(self, identifier: Optional[str] = None, identifier_type: Optional[str] = None) -> List[Breach]:
        """
        Retrieve breaches from database.
        
        Args:
            identifier: Optional identifier to filter by
            identifier_type: Optional identifier type to filter by
        
        Returns:
            List of Breach objects
        """
        session = self.get_session()
        try:
            query = session.query(Breach)
            
            if identifier:
                query = query.filter(Breach.identifier == identifier)
            if identifier_type:
                query = query.filter(Breach.identifier_type == identifier_type)
            
            return query.order_by(Breach.first_seen.desc()).all()
        finally:
            session.close()
    
    def record_check(self, identifier: str, identifier_type: str, breaches_found: int, 
                    new_breaches: int, updated_breaches: int, success: bool = True, 
                    error_message: Optional[str] = None):
        """
        Record a check in history.
        
        Args:
            identifier: Identifier that was checked
            identifier_type: Type of identifier
            breaches_found: Total breaches found
            new_breaches: Number of new breaches
            updated_breaches: Number of updated breaches
            success: Whether check was successful
            error_message: Error message if failed
        """
        session = self.get_session()
        try:
            check = CheckHistory(
                identifier=identifier,
                identifier_type=identifier_type,
                breaches_found=breaches_found,
                new_breaches=new_breaches,
                updated_breaches=updated_breaches,
                success=success,
                error_message=error_message
            )
            session.add(check)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording check history: {e}")
        finally:
            session.close()

