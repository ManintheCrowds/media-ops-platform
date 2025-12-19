"""Main application entry point for Pi client."""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

from .config import Config
from .client import PiAPIClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/pi-client/app.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class PiClientApp:
    """Main Pi client application."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize application."""
        self.config = Config.load(config_path)
        self.config.validate()
        self.running = False
        self._shutdown_event = asyncio.Event()
    
    async def start(self):
        """Start the application."""
        logger.info("Starting Pi Client Application")
        logger.info(f"Device ID: {self.config.device.device_id}")
        logger.info(f"API URL: {self.config.api.base_url}")
        
        self.running = True
        
        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._signal_handler)
        
        try:
            # Start main tasks
            await asyncio.gather(
                self._main_loop(),
                return_exceptions=True,
            )
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the application."""
        logger.info("Stopping Pi Client Application")
        self.running = False
        self._shutdown_event.set()
    
    def _signal_handler(self):
        """Handle shutdown signals."""
        logger.info("Received shutdown signal")
        asyncio.create_task(self.stop())
    
    async def _main_loop(self):
        """Main application loop."""
        # Import here to avoid circular dependencies
        from .cache.sync import SyncManager
        from .display.server import DisplayServer
        
        # Initialize components
        sync_manager = SyncManager(self.config)
        display_server = DisplayServer(self.config)
        
        # Start display server
        await display_server.start()
        
        # Start sync manager
        await sync_manager.start()
        
        # Wait for shutdown
        await self._shutdown_event.wait()
        
        # Stop components
        await sync_manager.stop()
        await display_server.stop()
        
        logger.info("Application stopped")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Raspberry Pi Client for Educational Platform")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="Pi Client 1.0.0",
    )
    
    args = parser.parse_args()
    
    app = PiClientApp(config_path=args.config)
    
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
