"""Cache management with LRU cache and TTL support."""

import logging
import time
from collections import OrderedDict
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from .storage import CacheStorage
from ..config import Config

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages content caching with LRU eviction and TTL."""
    
    def __init__(self, config: Config):
        """Initialize cache manager."""
        self.config = config
        self.storage = CacheStorage(config.cache.directory)
        self.max_size_bytes = config.cache.max_size_mb * 1024 * 1024
        self.ttl_seconds = config.cache.ttl_hours * 3600
        
        # LRU cache for metadata (in-memory)
        self._metadata_cache: OrderedDict[int, Dict[str, Any]] = OrderedDict()
        self._max_metadata_items = 1000
    
    def get_content(self, content_id: int) -> Optional[Dict[str, Any]]:
        """Get cached content metadata."""
        # Check in-memory cache first
        if content_id in self._metadata_cache:
            metadata = self._metadata_cache[content_id]
            self._metadata_cache.move_to_end(content_id)
            
            # Check TTL
            cached_at = datetime.fromisoformat(metadata.get("cached_at", ""))
            if datetime.now(timezone.utc) - cached_at < timedelta(seconds=self.ttl_seconds):
                return metadata
            else:
                # Expired, remove from cache
                del self._metadata_cache[content_id]
        
        # Check disk cache
        metadata = self.storage.load_metadata(content_id)
        if metadata:
            cached_at = datetime.fromisoformat(metadata.get("cached_at", ""))
            if datetime.now(timezone.utc) - cached_at < timedelta(seconds=self.ttl_seconds):
                # Add to in-memory cache
                self._add_to_metadata_cache(content_id, metadata)
                return metadata
            else:
                # Expired, delete
                self.storage.delete_content(content_id)
        
        return None
    
    def cache_content(self, content_id: int, metadata: Dict[str, Any]) -> bool:
        """Cache content metadata."""
        try:
            # Save to disk
            success = self.storage.save_metadata(content_id, metadata)
            if success:
                # Add to in-memory cache
                self._add_to_metadata_cache(content_id, metadata)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to cache content {content_id}: {e}")
            return False
    
    def get_media_file(self, content_id: int, filename: str) -> Optional[str]:
        """Get path to cached media file."""
        file_path = self.storage.get_media_file(content_id, filename)
        if file_path:
            return str(file_path)
        return None
    
    def cache_media_file(self, content_id: int, filename: str, data: bytes) -> Optional[str]:
        """Cache media file."""
        try:
            # Check cache size before caching
            if self._needs_cleanup():
                self._cleanup_cache()
            
            file_path = self.storage.save_media_file(content_id, filename, data)
            if file_path:
                return str(file_path)
            return None
        except Exception as e:
            logger.error(f"Failed to cache media file {filename} for content {content_id}: {e}")
            return None
    
    def invalidate_content(self, content_id: int) -> bool:
        """Invalidate cached content."""
        try:
            # Remove from in-memory cache
            if content_id in self._metadata_cache:
                del self._metadata_cache[content_id]
            
            # Remove from disk
            return self.storage.delete_content(content_id)
        except Exception as e:
            logger.error(f"Failed to invalidate content {content_id}: {e}")
            return False
    
    def _add_to_metadata_cache(self, content_id: int, metadata: Dict[str, Any]):
        """Add metadata to in-memory LRU cache."""
        if content_id in self._metadata_cache:
            self._metadata_cache.move_to_end(content_id)
        else:
            self._metadata_cache[content_id] = metadata
            # Evict oldest if cache is full
            if len(self._metadata_cache) > self._max_metadata_items:
                self._metadata_cache.popitem(last=False)
    
    def _needs_cleanup(self) -> bool:
        """Check if cache cleanup is needed."""
        current_size = self.storage.get_cache_size()
        return current_size > self.max_size_bytes
    
    def _cleanup_cache(self):
        """Clean up cache to free space."""
        logger.info("Cleaning up cache...")
        
        # First, try to delete expired files
        deleted = self.storage.cleanup_old_files(max_age_hours=self.config.cache.ttl_hours)
        logger.info(f"Deleted {deleted} expired files")
        
        # If still over limit, delete oldest files
        if self._needs_cleanup():
            logger.warning("Cache still over limit, deleting oldest files...")
            # This would implement more aggressive cleanup
            # For now, we'll just log a warning
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache_size = self.storage.get_cache_size()
        return {
            "size_bytes": cache_size,
            "size_mb": cache_size / (1024 * 1024),
            "max_size_mb": self.config.cache.max_size_mb,
            "usage_percent": (cache_size / self.max_size_bytes) * 100,
            "metadata_items": len(self._metadata_cache),
        }


