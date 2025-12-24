"""Display management with content rotation and mode switching."""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime, timedelta

from ..config import Config

logger = logging.getLogger(__name__)


class DisplayMode(str, Enum):
    """Display modes."""
    KIOSK = "kiosk"
    INTERACTIVE = "interactive"
    PRESENTATION = "presentation"
    DASHBOARD = "dashboard"


class DisplayManager:
    """Manages display modes, content rotation, and screen control."""
    
    def __init__(self, config: Config):
        """Initialize display manager."""
        self.config = config
        self.current_mode = DisplayMode(config.display.mode)
        self.rotation = config.display.rotation
        self.fullscreen = config.display.fullscreen
        
        self._rotation_task: Optional[asyncio.Task] = None
        self._content_queue: List[Dict[str, Any]] = []
        self._current_content_index = 0
        self._rotation_interval = 30  # seconds
        
    async def start(self):
        """Start display manager."""
        logger.info(f"Starting display manager in {self.current_mode.value} mode")
        
        if self.current_mode == DisplayMode.KIOSK:
            await self._start_content_rotation()
    
    async def stop(self):
        """Stop display manager."""
        if self._rotation_task:
            self._rotation_task.cancel()
            try:
                await self._rotation_task
            except asyncio.CancelledError:
                pass
    
    async def _start_content_rotation(self):
        """Start automatic content rotation for kiosk mode."""
        self._rotation_task = asyncio.create_task(self._rotation_loop())
    
    async def _rotation_loop(self):
        """Content rotation loop."""
        while True:
            try:
                if self._content_queue:
                    await self._rotate_to_next_content()
                await asyncio.sleep(self._rotation_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rotation loop: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _rotate_to_next_content(self):
        """Rotate to next content item."""
        if not self._content_queue:
            return
        
        self._current_content_index = (self._current_content_index + 1) % len(self._content_queue)
        content = self._content_queue[self._current_content_index]
        
        logger.info(f"Rotating to content: {content.get('id')}")
        # Emit event or update display
        # This would trigger a display update in the web UI
    
    def set_mode(self, mode: DisplayMode):
        """Switch display mode."""
        logger.info(f"Switching display mode to {mode.value}")
        self.current_mode = mode
        
        # Restart rotation if needed
        if mode == DisplayMode.KIOSK:
            asyncio.create_task(self._start_content_rotation())
        elif self._rotation_task:
            self._rotation_task.cancel()
    
    def set_rotation(self, rotation: str):
        """Set screen rotation."""
        self.rotation = rotation
        logger.info(f"Screen rotation set to {rotation}")
        # This would apply rotation to the display
    
    def set_fullscreen(self, fullscreen: bool):
        """Set fullscreen mode."""
        self.fullscreen = fullscreen
        logger.info(f"Fullscreen set to {fullscreen}")
        # This would apply fullscreen to the browser/display
    
    def set_content_queue(self, content_list: List[Dict[str, Any]]):
        """Set content queue for rotation."""
        self._content_queue = content_list
        self._current_content_index = 0
        logger.info(f"Content queue set with {len(content_list)} items")
    
    def get_current_content(self) -> Optional[Dict[str, Any]]:
        """Get current content being displayed."""
        if self._content_queue and 0 <= self._current_content_index < len(self._content_queue):
            return self._content_queue[self._current_content_index]
        return None
    
    def handle_touch_event(self, x: int, y: int, event_type: str = "click"):
        """Handle touch event."""
        if self.current_mode == DisplayMode.INTERACTIVE:
            logger.debug(f"Touch event: {event_type} at ({x}, {y})")
            # Process touch event
        elif self.current_mode == DisplayMode.KIOSK:
            # In kiosk mode, touch might advance to next content
            asyncio.create_task(self._rotate_to_next_content())







