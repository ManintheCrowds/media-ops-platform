"""Remote control via WebSocket."""

import asyncio
import json
import logging
from typing import Dict, Any, Set

from fastapi import WebSocket, WebSocketDisconnect

from ..config import Config
from .manager import DisplayManager, DisplayMode

logger = logging.getLogger(__name__)


class RemoteControl:
    """Handles remote control commands via WebSocket."""
    
    def __init__(self, config: Config, display_manager: DisplayManager):
        """Initialize remote control."""
        self.config = config
        self.display_manager = display_manager
        self.connections: Set[WebSocket] = set()
    
    async def handle_connection(self, websocket: WebSocket):
        """Handle WebSocket connection."""
        await websocket.accept()
        self.connections.add(websocket)
        logger.info("New WebSocket connection established")
        
        try:
            while True:
                # Receive command
                data = await websocket.receive_text()
                command = json.loads(data)
                
                # Process command
                response = await self._process_command(command)
                
                # Send response
                await websocket.send_json(response)
        
        except WebSocketDisconnect:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error handling WebSocket: {e}", exc_info=True)
        finally:
            self.connections.discard(websocket)
    
    async def _process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process remote control command."""
        cmd_type = command.get("type")
        
        try:
            if cmd_type == "navigate":
                return await self._handle_navigate(command)
            elif cmd_type == "playback":
                return await self._handle_playback(command)
            elif cmd_type == "display_mode":
                return await self._handle_display_mode(command)
            elif cmd_type == "settings":
                return await self._handle_settings(command)
            else:
                return {"status": "error", "message": f"Unknown command type: {cmd_type}"}
        
        except Exception as e:
            logger.error(f"Error processing command {cmd_type}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    async def _handle_navigate(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle navigation command."""
        action = command.get("action")
        
        if action == "next":
            await self.display_manager._rotate_to_next_content()
        elif action == "previous":
            # Implement previous content
            pass
        elif action == "goto":
            content_id = command.get("content_id")
            # Navigate to specific content
            pass
        
        return {"status": "success", "action": action}
    
    async def _handle_playback(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle playback control command."""
        action = command.get("action")  # play, pause, stop, seek
        
        # This would control media playback
        logger.info(f"Playback command: {action}")
        
        return {"status": "success", "action": action}
    
    async def _handle_display_mode(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle display mode change."""
        mode = command.get("mode")
        
        try:
            display_mode = DisplayMode(mode)
            self.display_manager.set_mode(display_mode)
            return {"status": "success", "mode": mode}
        except ValueError:
            return {"status": "error", "message": f"Invalid mode: {mode}"}
    
    async def _handle_settings(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle settings update."""
        setting = command.get("setting")
        value = command.get("value")
        
        if setting == "rotation":
            self.display_manager.set_rotation(value)
        elif setting == "fullscreen":
            self.display_manager.set_fullscreen(value)
        
        return {"status": "success", "setting": setting, "value": value}
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        disconnected = set()
        for connection in self.connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        self.connections -= disconnected



