"""Agent task model for multi-agent coordination."""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.sql import func
from app.database import Base


class AgentTask(Base):
    """Agent task for coordination and tracking."""
    
    __tablename__ = "agent_tasks"
    
    id = Column(String(255), primary_key=True, index=True)
    agent_type = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    status = Column(String(20), nullable=False, default="pending", index=True)
    priority = Column(Integer, default=0, index=True)
    dependencies = Column(JSON)  # List of task IDs
    assigned_agent = Column(String(100))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    result = Column(JSON)  # Agent execution results
    error = Column(Text)
    timeout = Column(Integer, default=300)  # seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_agent_tasks_status', 'status'),
        Index('idx_agent_tasks_agent_type', 'agent_type'),
        Index('idx_agent_tasks_priority', 'priority'),
    )


