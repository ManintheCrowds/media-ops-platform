"""Streaming service for media delivery."""

import os
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, AsyncIterator
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.content import ContentItem
from app.services.content_service import ContentService
from app.services.integrations.jellyfin_client import JellyfinClient


class StreamingService:
    """Service for streaming media content."""
    
    @staticmethod
    async def get_stream(
        db: Session,
        content_id: int,
        device_id: str,
        range_header: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get stream for content with range support.
        
        Args:
            db: Database session
            content_id: Content item ID
            device_id: Device ID
            range_header: HTTP Range header value
        
        Returns:
            Dictionary with stream information or None
        """
        # Get content item
        content = ContentService.get_content(db, content_id)
        if not content:
            return None
        
        # Check if content has media file
        metadata = content.metadata or {}
        media_file = metadata.get("media_file")
        external_refs = content.external_refs or {}
        
        # Try to get stream from external service (Jellyfin)
        if external_refs.get("jellyfin"):
            return await StreamingService._get_jellyfin_stream(
                external_refs["jellyfin"],
                range_header
            )
        
        # Try local file
        if media_file:
            return await StreamingService._get_file_stream(
                media_file,
                range_header
            )
        
        return None
    
    @staticmethod
    async def _get_file_stream(
        file_path: str,
        range_header: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get stream from local file."""
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return None
        
        file_size = path.stat().st_size
        content_type, _ = mimetypes.guess_type(str(path))
        if not content_type:
            content_type = "application/octet-stream"
        
        start = 0
        end = file_size - 1
        content_range = None
        
        # Parse range header
        if range_header:
            range_parts = range_header.replace("bytes=", "").split("-")
            if len(range_parts) == 2:
                if range_parts[0]:
                    start = int(range_parts[0])
                if range_parts[1]:
                    end = int(range_parts[1])
                else:
                    end = file_size - 1
                
                content_length = end - start + 1
                content_range = f"bytes {start}-{end}/{file_size}"
            else:
                content_length = file_size
        else:
            content_length = file_size
        
        # Create async file reader
        async def file_stream() -> AsyncIterator[bytes]:
            with open(path, "rb") as f:
                f.seek(start)
                remaining = content_length
                chunk_size = 8192
                
                while remaining > 0:
                    chunk = f.read(min(chunk_size, remaining))
                    if not chunk:
                        break
                    yield chunk
                    remaining -= len(chunk)
        
        return {
            "stream": file_stream(),
            "content_type": content_type,
            "content_length": content_length,
            "content_range": content_range,
            "file_size": file_size,
        }
    
    @staticmethod
    async def _get_jellyfin_stream(
        jellyfin_ref: Dict[str, Any],
        range_header: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get stream from Jellyfin."""
        item_id = jellyfin_ref.get("item_id")
        if not item_id:
            return None
        
        async with JellyfinClient() as client:
            stream_url = await client.get_stream_url(item_id)
            if not stream_url:
                return None
            
            # For Jellyfin, we'd proxy the stream
            # This is a simplified version
            import httpx
            
            headers = {}
            if range_header:
                headers["Range"] = range_header
            
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(stream_url, headers=headers, stream=True)
                
                async def stream() -> AsyncIterator[bytes]:
                    async for chunk in response.aiter_bytes():
                        yield chunk
                
                return {
                    "stream": stream(),
                    "content_type": response.headers.get("Content-Type", "video/mp4"),
                    "content_length": response.headers.get("Content-Length"),
                    "content_range": response.headers.get("Content-Range"),
                }
    
    @staticmethod
    async def get_stream_info(
        db: Session,
        content_id: int,
        device_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get stream metadata."""
        content = ContentService.get_content(db, content_id)
        if not content:
            return None
        
        metadata = content.metadata or {}
        external_refs = content.external_refs or {}
        
        # Get file size
        size = 0
        content_type = "application/octet-stream"
        
        if external_refs.get("jellyfin"):
            # Get info from Jellyfin
            item_id = external_refs["jellyfin"].get("item_id")
            if item_id:
                async with JellyfinClient() as client:
                    item = await client.get_item(item_id)
                    if item:
                        size = item.get("Size", 0)
                        media_type = item.get("MediaType")
                        if media_type == "Video":
                            content_type = "video/mp4"
        
        elif metadata.get("media_file"):
            path = Path(metadata["media_file"])
            if path.exists():
                size = path.stat().st_size
                content_type, _ = mimetypes.guess_type(str(path))
                if not content_type:
                    content_type = "application/octet-stream"
        
        return {
            "content_id": content_id,
            "size": size,
            "content_type": content_type,
            "supports_range": True,
        }







