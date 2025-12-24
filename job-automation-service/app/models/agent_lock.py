"""Agent lock model for task coordination."""

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base


class AgentLock(Base):
    """Lock for agent task coordination."""
    
    __tablename__ = "agent_locks"
    
    task_id = Column(String(255), ForeignKey("agent_tasks.id"), primary_key=True)
    agent_id = Column(String(100), nullable=False)
    acquired_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    lock_token = Column(String(255), unique=True, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_agent_locks_expires', 'expires_at'),
    )


