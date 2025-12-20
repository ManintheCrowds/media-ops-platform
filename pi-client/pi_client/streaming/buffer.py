"""Buffering strategy for streaming."""

import asyncio
import logging
from typing import Optional, Deque
from collections import deque
import time

logger = logging.getLogger(__name__)


class BufferManager:
    """Manages streaming buffer with adaptive strategies."""
    
    def __init__(self, min_buffer_size: int = 2 * 1024 * 1024, max_buffer_size: int = 10 * 1024 * 1024):
        """Initialize buffer manager.
        
        Args:
            min_buffer_size: Minimum buffer size in bytes before playback
            max_buffer_size: Maximum buffer size in bytes
        """
        self.min_buffer_size = min_buffer_size
        self.max_buffer_size = max_buffer_size
        self.buffer: Deque[bytes] = deque()
        self.buffer_size = 0
        self.is_playing = False
        self._buffer_lock = asyncio.Lock()
    
    async def add_chunk(self, chunk: bytes):
        """Add chunk to buffer."""
        async with self._buffer_lock:
            # Don't exceed max buffer size
            while self.buffer_size + len(chunk) > self.max_buffer_size and self.buffer:
                removed = self.buffer.popleft()
                self.buffer_size -= len(removed)
            
            self.buffer.append(chunk)
            self.buffer_size += len(chunk)
    
    async def get_chunk(self, size: Optional[int] = None) -> Optional[bytes]:
        """Get chunk from buffer."""
        async with self._buffer_lock:
            if not self.buffer:
                return None
            
            if size is None:
                chunk = self.buffer.popleft()
                self.buffer_size -= len(chunk)
                return chunk
            
            # Get chunks until we have enough data
            chunks = []
            total_size = 0
            while total_size < size and self.buffer:
                chunk = self.buffer.popleft()
                chunks.append(chunk)
                total_size += len(chunk)
                self.buffer_size -= len(chunk)
            
            if chunks:
                return b"".join(chunks)
            return None
    
    def has_minimum_buffer(self) -> bool:
        """Check if buffer has minimum required data."""
        return self.buffer_size >= self.min_buffer_size
    
    def get_buffer_health(self) -> float:
        """Get buffer health (0.0 = empty, 1.0 = full)."""
        if self.max_buffer_size == 0:
            return 0.0
        return min(1.0, self.buffer_size / self.max_buffer_size)
    
    def clear(self):
        """Clear buffer."""
        self.buffer.clear()
        self.buffer_size = 0
    
    def get_stats(self) -> dict:
        """Get buffer statistics."""
        return {
            "size_bytes": self.buffer_size,
            "size_mb": self.buffer_size / (1024 * 1024),
            "chunks": len(self.buffer),
            "health": self.get_buffer_health(),
            "has_minimum": self.has_minimum_buffer(),
        }


