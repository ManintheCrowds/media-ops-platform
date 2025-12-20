"""Local storage operations for cache."""

import os
import json
import hashlib
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


class CacheStorage:
    """Manages local file storage for cached content."""
    
    def __init__(self, cache_dir: str):
        """Initialize cache storage."""
        self.cache_dir = Path(cache_dir)
        self.metadata_dir = self.cache_dir / "metadata"
        self.media_dir = self.cache_dir / "media"
        self.sync_dir = self.cache_dir / "sync" / "packages"
        
        # Create directories
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.sync_dir.mkdir(parents=True, exist_ok=True)
    
    def get_metadata_path(self, content_id: int) -> Path:
        """Get path for content metadata."""
        return self.metadata_dir / f"content_{content_id}.json"
    
    def get_media_path(self, content_id: int, filename: str = None) -> Path:
        """Get path for media file."""
        content_dir = self.media_dir / str(content_id)
        content_dir.mkdir(parents=True, exist_ok=True)
        if filename:
            return content_dir / filename
        return content_dir
    
    def save_metadata(self, content_id: int, metadata: Dict[str, Any]) -> bool:
        """Save content metadata."""
        try:
            metadata_path = self.get_metadata_path(content_id)
            metadata["cached_at"] = datetime.now(timezone.utc).isoformat()
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save metadata for content {content_id}: {e}")
            return False
    
    def load_metadata(self, content_id: int) -> Optional[Dict[str, Any]]:
        """Load content metadata."""
        try:
            metadata_path = self.get_metadata_path(content_id)
            if not metadata_path.exists():
                return None
            
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            return metadata
        except Exception as e:
            logger.error(f"Failed to load metadata for content {content_id}: {e}")
            return None
    
    def save_media_file(self, content_id: int, filename: str, data: bytes) -> Optional[Path]:
        """Save media file."""
        try:
            file_path = self.get_media_path(content_id, filename)
            with open(file_path, "wb") as f:
                f.write(data)
            return file_path
        except Exception as e:
            logger.error(f"Failed to save media file {filename} for content {content_id}: {e}")
            return None
    
    def get_media_file(self, content_id: int, filename: str) -> Optional[Path]:
        """Get path to media file if it exists."""
        file_path = self.get_media_path(content_id, filename)
        if file_path.exists():
            return file_path
        return None
    
    def delete_content(self, content_id: int) -> bool:
        """Delete all cached data for content."""
        try:
            # Delete metadata
            metadata_path = self.get_metadata_path(content_id)
            if metadata_path.exists():
                metadata_path.unlink()
            
            # Delete media directory
            media_path = self.get_media_path(content_id)
            if media_path.exists() and media_path.is_dir():
                shutil.rmtree(media_path)
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete content {content_id}: {e}")
            return False
    
    def get_cache_size(self) -> int:
        """Get total cache size in bytes."""
        total_size = 0
        for dir_path in [self.metadata_dir, self.media_dir, self.sync_dir]:
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
        return total_size
    
    def cleanup_old_files(self, max_age_hours: int = 168) -> int:
        """Clean up files older than max_age_hours. Returns number of files deleted."""
        deleted_count = 0
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        for dir_path in [self.metadata_dir, self.media_dir]:
            if not dir_path.exists():
                continue
            
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    try:
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if mtime < cutoff_time:
                            file_path.unlink()
                            deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete {file_path}: {e}")
        
        return deleted_count
    
    def get_package_path(self, package_id: int) -> Path:
        """Get path for sync package."""
        return self.sync_dir / f"package_{package_id}.tar.gz"
    
    def save_package(self, package_id: int, data: bytes) -> Optional[Path]:
        """Save sync package."""
        try:
            package_path = self.get_package_path(package_id)
            with open(package_path, "wb") as f:
                f.write(data)
            return package_path
        except Exception as e:
            logger.error(f"Failed to save package {package_id}: {e}")
            return None


