"""Web UI server for Pi client."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
import uvicorn

from ..config import Config
from .manager import DisplayManager
from .remote import RemoteControl

logger = logging.getLogger(__name__)


class DisplayServer:
    """Web-based UI server for Pi client."""
    
    def __init__(self, config: Config):
        """Initialize display server."""
        self.config = config
        self.app = FastAPI(title="Pi Client Display")
        self.display_manager = DisplayManager(config)
        self.remote_control = RemoteControl(config, self.display_manager)
        self._server_task: Optional[asyncio.Task] = None
        
        # Setup templates
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Dashboard view."""
            template = self.jinja_env.get_template("dashboard.html")
            return HTMLResponse(template.render(config=self.config))
        
        @self.app.get("/content", response_class=HTMLResponse)
        async def content_browser(request: Request):
            """Content browser view."""
            template = self.jinja_env.get_template("content.html")
            return HTMLResponse(template.render(config=self.config))
        
        @self.app.get("/content/{content_id}", response_class=HTMLResponse)
        async def content_viewer(request: Request, content_id: int):
            """Content viewer."""
            template = self.jinja_env.get_template("viewer.html")
            return HTMLResponse(template.render(content_id=content_id, config=self.config))
        
        @self.app.get("/settings", response_class=HTMLResponse)
        async def settings(request: Request):
            """Settings page."""
            template = self.jinja_env.get_template("settings.html")
            return HTMLResponse(template.render(config=self.config))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await self.remote_control.handle_connection(websocket)
        
        @self.app.get("/api/status")
        async def get_status():
            """Get device status."""
            return {
                "device_id": self.config.device.device_id,
                "display_mode": self.display_manager.current_mode,
                "status": "running",
            }
        
        @self.app.get("/api/content")
        async def get_content_list():
            """Get content list."""
            # This would fetch from cache or API
            return {"content": []}
    
    async def start(self):
        """Start the display server."""
        logger.info(f"Starting display server on port {self.config.display.port}")
        
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.config.display.port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        
        self._server_task = asyncio.create_task(server.serve())
    
    async def stop(self):
        """Stop the display server."""
        logger.info("Stopping display server")
        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
