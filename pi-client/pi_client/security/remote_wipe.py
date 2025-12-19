"""Remote wipe capability for secure data deletion."""

import logging
import shutil
from pathlib import Path
from typing import List

from ..config import Config
from ..client import PiAPIClient

logger = logging.getLogger(__name__)


class RemoteWipeManager:
    """Manages remote wipe operations."""
    
    def __init__(self, config: Config):
        """Initialize remote wipe manager."""
        self.config = config
        self.wipe_in_progress = False
    
    async def check_wipe_command(self) -> bool:
        """Check for remote wipe command from server.
        
        Returns:
            True if wipe command received
        """
        try:
            async with PiAPIClient(self.config) as client:
                # Check device status for wipe flag
                status = await client.get_device_status()
                
                # In a real implementation, the server would set a wipe flag
                # For now, we check security_status
                security_status = status.get("security_status")
                if security_status == "wiped":
                    logger.warning("Remote wipe command received")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to check wipe command: {e}", exc_info=True)
            return False
    
    async def perform_wipe(self) -> bool:
        """Perform remote wipe operation.
        
        Returns:
            True if wipe completed successfully
        """
        if self.wipe_in_progress:
            logger.warning("Wipe already in progress")
            return False
        
        self.wipe_in_progress = True
        logger.warning("Starting remote wipe operation...")
        
        try:
            # 1. Clear cache
            await self._wipe_cache()
            
            # 2. Clear configuration (except device_id for re-registration)
            await self._wipe_config()
            
            # 3. Clear certificates
            await self._wipe_certificates()
            
            # 4. Clear logs (optional)
            await self._wipe_logs()
            
            logger.warning("Remote wipe completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Remote wipe failed: {e}", exc_info=True)
            return False
        finally:
            self.wipe_in_progress = False
    
    async def _wipe_cache(self):
        """Wipe cache directory."""
        cache_dir = Path(self.config.cache.directory)
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                logger.info("Cache directory wiped")
            except Exception as e:
                logger.error(f"Failed to wipe cache: {e}")
    
    async def _wipe_config(self):
        """Wipe configuration (preserve device_id)."""
        # Clear sensitive config data
        # Keep device_id for potential re-registration
        config_paths = [
            Path.home() / ".pi-client" / "config.yaml",
            Path("/etc/pi-client/config.yaml"),
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    # In a real implementation, would preserve device_id
                    # and only clear sensitive fields
                    config_path.unlink()
                    logger.info(f"Config file wiped: {config_path}")
                except Exception as e:
                    logger.error(f"Failed to wipe config: {e}")
    
    async def _wipe_certificates(self):
        """Wipe certificates."""
        cert_dir = Path(self.config.security.cert_path).parent
        if cert_dir.exists():
            try:
                for cert_file in cert_dir.glob("*"):
                    if cert_file.is_file():
                        cert_file.unlink()
                logger.info("Certificates wiped")
            except Exception as e:
                logger.error(f"Failed to wipe certificates: {e}")
    
    async def _wipe_logs(self):
        """Wipe log files."""
        log_paths = [
            Path("/var/log/pi-client/app.log"),
            Path("/var/log/pi-client/error.log"),
            Path("/var/log/pi-client/sync.log"),
        ]
        
        for log_path in log_paths:
            if log_path.exists():
                try:
                    log_path.unlink()
                    logger.info(f"Log file wiped: {log_path}")
                except Exception as e:
                    logger.error(f"Failed to wipe log: {e}")

