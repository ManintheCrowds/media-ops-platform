"""Streaming client with HTTP range request support."""

import asyncio
import aiofiles
import logging
import time
from typing import Optional, AsyncIterator
from pathlib import Path

from ..config import Config
from ..client import PiAPIClient
from .buffer import BufferManager
from .quality import QualityManager, QualityLevel

logger = logging.getLogger(__name__)


class StreamingClient:
    """Client for streaming media with adaptive quality and buffering."""
    
    def __init__(self, config: Config):
        """Initialize streaming client."""
        self.config = config
        self.buffer_manager = BufferManager()
        self.quality_manager = QualityManager()
        self.chunk_size = 1024 * 1024  # 1MB default
        self._streaming = False
        self._download_speed = 0.0
    
    async def stream_content(
        self,
        content_id: int,
        output_path: Optional[str] = None,
        quality: Optional[QualityLevel] = None
    ) -> AsyncIterator[bytes]:
        """Stream content with adaptive quality.
        
        Args:
            content_id: Content item ID
            output_path: Optional path to save streamed content
            quality: Optional quality level override
        
        Yields:
            Chunks of media data
        """
        self._streaming = True
        
        try:
            async with PiAPIClient(self.config) as client:
                # Get stream info
                stream_info = await client.get_stream_info(content_id)
                total_size = stream_info.get("size", 0)
                
                # Get quality parameters
                quality_params = self.quality_manager.get_quality_params(quality)
                self.chunk_size = quality_params.get("chunk_size", self.chunk_size)
                
                # Start streaming
                current_position = 0
                download_start = time.time()
                bytes_downloaded = 0
                
                while self._streaming and (total_size == 0 or current_position < total_size):
                    # Calculate end position
                    end_position = current_position + self.chunk_size - 1
                    if total_size > 0:
                        end_position = min(end_position, total_size - 1)
                    
                    # Request chunk
                    try:
                        response = await client.stream_media(
                            content_id,
                            start_byte=current_position,
                            end_byte=end_position
                        )
                        
                        chunk = response.content
                        chunk_size = len(chunk)
                        
                        if chunk_size == 0:
                            break
                        
                        # Update download speed
                        elapsed = time.time() - download_start
                        if elapsed > 0:
                            bytes_downloaded += chunk_size
                            speed_mbps = (bytes_downloaded * 8) / (elapsed * 1_000_000)
                            self.quality_manager.update_network_speed(speed_mbps)
                        
                        # Add to buffer
                        await self.buffer_manager.add_chunk(chunk)
                        
                        # Update buffer health
                        buffer_health = self.buffer_manager.get_buffer_health()
                        self.quality_manager.update_buffer_health(buffer_health)
                        
                        # Adjust quality if needed
                        if self.quality_manager.current_quality == QualityLevel.AUTO:
                            recommended = self.quality_manager.get_recommended_quality()
                            if recommended != self.quality_manager.current_quality:
                                logger.info(f"Adjusting quality to {recommended.value}")
                                # Could restart stream with new quality here
                        
                        # Yield chunk
                        yield chunk
                        
                        # Save to file if output path provided
                        if output_path:
                            async with aiofiles.open(output_path, "ab") as f:
                                await f.write(chunk)
                        
                        current_position += chunk_size
                        
                        # Wait for buffer if needed
                        if not self.buffer_manager.has_minimum_buffer():
                            await asyncio.sleep(0.1)
                    
                    except Exception as e:
                        logger.error(f"Error streaming chunk at position {current_position}: {e}")
                        # Retry with smaller chunk
                        if self.chunk_size > 256 * 1024:
                            self.chunk_size = self.chunk_size // 2
                        await asyncio.sleep(1)
                
        finally:
            self._streaming = False
    
    async def stream_to_file(
        self,
        content_id: int,
        output_path: str,
        quality: Optional[QualityLevel] = None
    ) -> bool:
        """Stream content directly to file."""
        try:
            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Clear existing file
            if output_file.exists():
                output_file.unlink()
            
            # Stream and save
            async for chunk in self.stream_content(content_id, output_path, quality):
                pass  # Chunks are saved in stream_content
            
            return output_file.exists()
            
        except Exception as e:
            logger.error(f"Failed to stream to file: {e}", exc_info=True)
            return False
    
    def stop_streaming(self):
        """Stop current streaming operation."""
        self._streaming = False
        self.buffer_manager.clear()
    
    def get_stats(self) -> dict:
        """Get streaming statistics."""
        return {
            "streaming": self._streaming,
            "download_speed_mbps": self._download_speed,
            "buffer": self.buffer_manager.get_stats(),
            "quality": self.quality_manager.get_recommended_quality().value,
        }
