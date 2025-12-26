"""Logging configuration with Loki integration."""

import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import httpx


class LokiHandler(logging.Handler):
    """Custom logging handler that sends logs to Loki."""
    
    def __init__(self, loki_url: Optional[str] = None):
        """
        Initialize Loki handler.
        
        Args:
            loki_url: Loki push API URL
        """
        super().__init__()
        self.loki_url = loki_url or os.getenv("LOKI_URL")
        self.enabled = bool(self.loki_url)
    
    def emit(self, record: logging.LogRecord):
        """Emit log record to Loki."""
        if not self.enabled:
            return
        
        try:
            # Format log entry
            log_entry = {
                "streams": [{
                    "stream": {
                        "service": "breach-monitor",
                        "level": record.levelname.lower(),
                        "identifier_type": getattr(record, "identifier_type", "unknown")
                    },
                    "values": [[
                        str(int(datetime.now().timestamp() * 1e9)),  # Nanoseconds
                        self.format(record)
                    ]]
                }]
            }
            
            # Send to Loki (async, fire and forget)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # If loop is running, schedule coroutine
                asyncio.create_task(self._send_to_loki(log_entry))
            else:
                # If loop not running, run it
                loop.run_until_complete(self._send_to_loki(log_entry))
                
        except Exception as e:
            # Don't let logging errors break the application
            print(f"Loki logging error: {e}")
    
    async def _send_to_loki(self, log_entry: Dict[str, Any]):
        """Send log entry to Loki."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    self.loki_url,
                    json=log_entry,
                    headers={"Content-Type": "application/json"}
                )
        except Exception:
            # Silently fail - logging should not break the app
            pass


def setup_logging(log_level: str = "INFO", loki_url: Optional[str] = None):
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        loki_url: Optional Loki URL for log aggregation
    """
    # Get log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    # Loki handler (if enabled)
    loki_handler = None
    if loki_url or os.getenv("LOKI_URL"):
        loki_handler = LokiHandler(loki_url)
        loki_handler.setLevel(level)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    if loki_handler:
        root_logger.addHandler(loki_handler)
    
    # Set levels for third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

