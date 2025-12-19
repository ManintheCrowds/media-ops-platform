"""Sync manager for content synchronization."""

import asyncio
import logging
import tarfile
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..config import Config
from ..client import PiAPIClient
from .manager import CacheManager
from .storage import CacheStorage

logger = logging.getLogger(__name__)


class SyncManager:
    """Manages content synchronization with the server."""
    
    def __init__(self, config: Config):
        """Initialize sync manager."""
        self.config = config
        self.cache_manager = CacheManager(config)
        self.running = False
        self._sync_task: Optional[asyncio.Task] = None
        self._last_sync: Optional[datetime] = None
    
    async def start(self):
        """Start sync manager."""
        logger.info("Starting sync manager")
        self.running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
    
    async def stop(self):
        """Stop sync manager."""
        logger.info("Stopping sync manager")
        self.running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
    
    async def _sync_loop(self):
        """Main sync loop."""
        while self.running:
            try:
                await self.check_and_sync()
                await asyncio.sleep(self.config.sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync error: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait before retrying
    
    async def check_and_sync(self) -> bool:
        """Check for updates and sync if needed."""
        try:
            async with PiAPIClient(self.config) as client:
                # Check for updates
                sync_status = await client.check_sync()
                
                if not sync_status.get("has_updates", False):
                    logger.debug("No updates available")
                    return False
                
                # Get available packages
                packages = sync_status.get("available_packages", [])
                if not packages:
                    return False
                
                # Process packages
                for package_info in packages:
                    await self._process_package(client, package_info)
                
                self._last_sync = datetime.utcnow()
                return True
                
        except Exception as e:
            logger.error(f"Failed to check sync: {e}", exc_info=True)
            return False
    
    async def _process_package(
        self,
        client: PiAPIClient,
        package_info: Dict[str, Any]
    ):
        """Process a sync package."""
        package_id = package_info.get("id")
        package_type = package_info.get("package_type")
        
        logger.info(f"Processing package {package_id} (type: {package_type})")
        
        try:
            # Download package
            package_path = await client.download_package(package_id)
            
            # Verify checksum if available
            if package_info.get("checksum"):
                if not self._verify_checksum(package_path, package_info["checksum"]):
                    logger.error(f"Checksum verification failed for package {package_id}")
                    return
            
            # Extract package
            await self._extract_package(package_path, package_id)
            
            # Mark sync complete
            await client._request(
                "POST",
                f"/devices/{self.config.device.device_id}/sync/complete",
                json={"package_id": package_id}
            )
            
            logger.info(f"Successfully processed package {package_id}")
            
        except Exception as e:
            logger.error(f"Failed to process package {package_id}: {e}", exc_info=True)
    
    def _verify_checksum(self, file_path: str, expected_checksum: str) -> bool:
        """Verify file checksum."""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            calculated = sha256.hexdigest()
            return calculated == expected_checksum
        except Exception as e:
            logger.error(f"Failed to verify checksum: {e}")
            return False
    
    async def _extract_package(self, package_path: str, package_id: int):
        """Extract sync package."""
        try:
            with tarfile.open(package_path, "r:gz") as tar:
                # Extract to cache directory
                extract_path = self.cache_manager.storage.cache_dir / "extracted" / str(package_id)
                extract_path.mkdir(parents=True, exist_ok=True)
                
                tar.extractall(extract_path)
                
                # Process extracted files
                await self._process_extracted_files(extract_path)
                
                # Clean up
                import shutil
                shutil.rmtree(extract_path)
                
        except Exception as e:
            logger.error(f"Failed to extract package {package_id}: {e}", exc_info=True)
            raise
    
    async def _process_extracted_files(self, extract_path: Path):
        """Process files extracted from sync package."""
        # Look for metadata and media files
        for item in extract_path.rglob("*"):
            if item.is_file():
                # Determine content ID from path structure
                # Assuming structure: content_{id}/metadata.json or content_{id}/media/{filename}
                parts = item.relative_to(extract_path).parts
                if len(parts) >= 2 and parts[0].startswith("content_"):
                    try:
                        content_id = int(parts[0].split("_")[1])
                        
                        if parts[1] == "metadata.json":
                            # Load and cache metadata
                            import json
                            with open(item, "r") as f:
                                metadata = json.load(f)
                            self.cache_manager.cache_content(content_id, metadata)
                        
                        elif parts[1] == "media":
                            # Cache media file
                            filename = parts[2] if len(parts) > 2 else item.name
                            with open(item, "rb") as f:
                                data = f.read()
                            self.cache_manager.cache_media_file(content_id, filename, data)
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Could not parse content ID from path {item}: {e}")
    
    async def request_full_sync(self) -> bool:
        """Request a full sync."""
        try:
            async with PiAPIClient(self.config) as client:
                package = await client.request_sync(package_type="full")
                if package:
                    await self._process_package(client, package)
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to request full sync: {e}", exc_info=True)
            return False
    
    async def request_incremental_sync(self, content_ids: Optional[List[int]] = None) -> bool:
        """Request an incremental sync."""
        try:
            async with PiAPIClient(self.config) as client:
                package = await client.request_sync(
                    package_type="incremental",
                    content_ids=content_ids
                )
                if package:
                    await self._process_package(client, package)
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to request incremental sync: {e}", exc_info=True)
            return False

