"""Database-based lock manager for agent coordination."""

import hashlib
import logging
import time
import os
import sys
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
from app.models.agent_lock import AgentLock
from app.models.agent_task import AgentTask
from tests.agents.config import config

logger = logging.getLogger(__name__)


class DatabaseLock:
    """Database-based lock using PostgreSQL advisory locks."""
    
    def __init__(
        self,
        task_id: str,
        agent_id: str,
        timeout: int = None,
        expiration: int = None
    ):
        """Initialize database lock.
        
        Args:
            task_id: Task identifier
            agent_id: Agent identifier
            timeout: Seconds to wait for lock (defaults to config)
            expiration: Seconds before lock expires (defaults to config)
        """
        self.task_id = task_id
        self.agent_id = agent_id
        self.timeout = timeout or config.lock_timeout
        self.expiration = expiration or config.lock_expiration
        self.lock_token = self._generate_token()
        self.lock_key = self._generate_lock_key(task_id)
        self.db: Optional[Session] = None
    
    def _generate_token(self) -> str:
        """Generate unique lock token."""
        return hashlib.sha256(
            f"{self.task_id}{self.agent_id}{time.time()}".encode()
        ).hexdigest()
    
    def _generate_lock_key(self, task_id: str) -> int:
        """Generate PostgreSQL advisory lock key from task_id."""
        # PostgreSQL advisory locks use bigint (64-bit)
        # Use hash to convert string to integer
        hash_obj = hashlib.sha256(task_id.encode())
        # Take first 8 bytes and convert to signed int64
        key_bytes = hash_obj.digest()[:8]
        # Convert to signed integer (PostgreSQL uses signed bigint)
        key = int.from_bytes(key_bytes, byteorder='big', signed=True)
        return key
    
    def _cleanup_expired_locks(self, db: Session):
        """Clean up expired locks."""
        try:
            now = datetime.utcnow()
            expired = db.query(AgentLock).filter(
                AgentLock.expires_at < now
            ).all()
            
            for lock in expired:
                # Release advisory lock if still held
                try:
                    db.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": self._generate_lock_key(lock.task_id)})
                except:
                    pass
                db.delete(lock)
            
            db.commit()
        except Exception as e:
            logger.warning(f"Error cleaning up expired locks: {e}")
            db.rollback()
    
    def __enter__(self):
        """Acquire lock."""
        self.db = SessionLocal()
        start_time = time.time()
        
        # Cleanup expired locks first
        self._cleanup_expired_locks(self.db)
        
        while True:
            try:
                # Try to acquire PostgreSQL advisory lock
                result = self.db.execute(
                    text("SELECT pg_try_advisory_lock(:key)"),
                    {"key": self.lock_key}
                ).scalar()
                
                if result:
                    # Lock acquired, create lock record
                    expires_at = datetime.utcnow() + timedelta(seconds=self.expiration)
                    
                    # Check if lock record exists
                    existing = self.db.query(AgentLock).filter(
                        AgentLock.task_id == self.task_id
                    ).first()
                    
                    if existing:
                        # Update existing lock
                        existing.agent_id = self.agent_id
                        existing.acquired_at = datetime.utcnow()
                        existing.expires_at = expires_at
                        existing.lock_token = self.lock_token
                    else:
                        # Create new lock
                        lock = AgentLock(
                            task_id=self.task_id,
                            agent_id=self.agent_id,
                            acquired_at=datetime.utcnow(),
                            expires_at=expires_at,
                            lock_token=self.lock_token
                        )
                        self.db.add(lock)
                    
                    self.db.commit()
                    logger.debug(f"Lock acquired for task {self.task_id}")
                    return self
                else:
                    # Lock not available, check timeout
                    elapsed = time.time() - start_time
                    if elapsed > self.timeout:
                        raise TimeoutError(
                            f"Could not acquire lock for {self.task_id} after {self.timeout}s"
                        )
                    time.sleep(0.1)  # Wait before retry
                    
            except Exception as e:
                if isinstance(e, TimeoutError):
                    raise
                logger.error(f"Error acquiring lock: {e}")
                # Fallback to file-based locking if enabled
                if config.enable_file_lock_fallback:
                    return self._file_lock_fallback()
                raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release lock."""
        try:
            if self.db:
                # Release advisory lock
                try:
                    self.db.execute(
                        text("SELECT pg_advisory_unlock(:key)"),
                        {"key": self.lock_key}
                    )
                except Exception as e:
                    logger.warning(f"Error releasing advisory lock: {e}")
                
                # Remove lock record
                lock = self.db.query(AgentLock).filter(
                    AgentLock.task_id == self.task_id,
                    AgentLock.lock_token == self.lock_token
                ).first()
                
                if lock:
                    self.db.delete(lock)
                    self.db.commit()
                
                self.db.close()
        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
            if self.db:
                self.db.rollback()
                self.db.close()
    
    def _file_lock_fallback(self):
        """Fallback to file-based locking."""
        logger.warning("Using file-based lock fallback")
        config.lock_dir.mkdir(parents=True, exist_ok=True)
        lock_file = config.lock_dir / f"{self.task_id}.lock"
        
        if sys.platform == "win32":
            import msvcrt
            self.lock_file_handle = open(lock_file, 'w')
            msvcrt.locking(self.lock_file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            self.lock_file_handle = open(lock_file, 'w')
            fcntl.flock(self.lock_file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        self.lock_file_handle.write(self.lock_token)
        self.lock_file_handle.flush()
        return self
    
    def validate(self, db: Session) -> bool:
        """Validate lock is still valid."""
        lock = db.query(AgentLock).filter(
            AgentLock.task_id == self.task_id,
            AgentLock.lock_token == self.lock_token
        ).first()
        
        if not lock:
            return False
        
        if lock.expires_at < datetime.utcnow():
            return False
        
        return True


