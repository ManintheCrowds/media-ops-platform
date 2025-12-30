"""Service for recording camera feeds using video encoders."""

from typing import Dict, Optional
from sqlalchemy.orm import Session
import logging

from .arlo_service import ArloService
from services.video_encoder.encoder_service import VideoEncoderService
from services.media_server.jellyfin_client import JellyfinClient
from app.exceptions import ArloCameraError, EncoderError

logger = logging.getLogger(__name__)


class CameraRecordingService:
    """Service for recording camera feeds via video encoders."""
    
    def __init__(self):
        """Initialize camera recording service."""
        self.arlo_service = ArloService()
        self.encoder_service = VideoEncoderService()
        self.media_client = None  # Optional Jellyfin client
    
    async def record_camera(
        self,
        db: Session,
        camera_id: int,
        encoder_id: int,
        duration: int = 3600  # 1 hour default
    ) -> Dict:
        """Record Arlo camera to local storage via encoder."""
        try:
            # Get camera stream URL
            camera = await self.arlo_service.get_camera(db, camera_id)
            stream = await self.arlo_service.start_live_stream(db, camera_id)
            stream_url = stream.get('stream_url')
            
            if not stream_url:
                raise ArloCameraError(
                    f"Could not get stream URL for camera {camera_id}",
                    camera_id=str(camera_id)
                )
            
            # Record via encoder
            recording = await self.encoder_service.record_stream(
                db=db,
                encoder_id=encoder_id,
                source_url=stream_url,
                output_path=None,  # Use default path
                duration=duration
            )
            
            # Optionally upload to media server if configured
            if self.media_client and recording.get('status') == 'recording':
                try:
                    # Upload would happen after recording completes
                    # For now, just log the intent
                    logger.info(f"Recording started, will upload to media server when complete: {recording.get('output_path')}")
                except Exception as e:
                    logger.warning(f"Failed to prepare media server upload: {str(e)}")
            
            return recording
            
        except Exception as e:
            logger.error(f"Failed to record camera {camera_id}: {str(e)}")
            raise

    async def stop_recording(
        self,
        db: Session,
        encoder_id: int
    ) -> Dict:
        """Stop recording on encoder."""
        return await self.encoder_service.stop_recording(db, encoder_id)

