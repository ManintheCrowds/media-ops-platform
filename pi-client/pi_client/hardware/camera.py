"""Camera interface for photo and video capture."""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import camera library
try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False
    logger.warning("picamera2 not available. Camera functionality will be disabled.")


class CameraInterface:
    """Interface for Raspberry Pi camera operations."""
    
    def __init__(self, enabled: bool = True):
        """Initialize camera interface."""
        self.enabled = enabled and CAMERA_AVAILABLE
        self.camera: Optional[Any] = None
        
        if self.enabled:
            try:
                self.camera = Picamera2()
                self.camera.start()
                logger.info("Camera initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize camera: {e}")
                self.enabled = False
                self.camera = None
    
    def capture_photo(
        self,
        output_path: Optional[str] = None,
        resolution: Optional[tuple] = None,
        quality: int = 85
    ) -> Optional[str]:
        """Capture a photo.
        
        Args:
            output_path: Path to save photo. If None, generates filename.
            resolution: Optional (width, height) tuple
            quality: JPEG quality (1-100)
        
        Returns:
            Path to saved photo or None if failed
        """
        if not self.enabled or not self.camera:
            logger.warning("Camera is not available")
            return None
        
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"/tmp/photo_{timestamp}.jpg"
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Configure camera if resolution specified
            if resolution:
                config = self.camera.create_still_configuration(main={"size": resolution})
                self.camera.configure(config)
            
            # Capture photo
            self.camera.capture_file(str(output_file))
            
            logger.info(f"Photo captured: {output_path}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to capture photo: {e}", exc_info=True)
            return None
    
    def start_video_recording(
        self,
        output_path: str,
        resolution: Optional[tuple] = None,
        framerate: int = 30
    ) -> bool:
        """Start video recording.
        
        Args:
            output_path: Path to save video
            resolution: Optional (width, height) tuple
            framerate: Frames per second
        
        Returns:
            True if started successfully
        """
        if not self.enabled or not self.camera:
            logger.warning("Camera is not available")
            return False
        
        try:
            # Configure for video
            if resolution:
                config = self.camera.create_video_configuration(main={"size": resolution})
            else:
                config = self.camera.create_video_configuration()
            
            self.camera.configure(config)
            self.camera.start_recording(output_path)
            
            logger.info(f"Video recording started: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start video recording: {e}", exc_info=True)
            return False
    
    def stop_video_recording(self) -> Optional[str]:
        """Stop video recording.
        
        Returns:
            Path to recorded video or None
        """
        if not self.enabled or not self.camera:
            return None
        
        try:
            self.camera.stop_recording()
            logger.info("Video recording stopped")
            # Return the last recorded file path
            # This would need to be tracked separately
            return None
        except Exception as e:
            logger.error(f"Failed to stop video recording: {e}", exc_info=True)
            return None
    
    def capture_timelapse(
        self,
        output_dir: str,
        interval: int = 5,
        duration: int = 60,
        resolution: Optional[tuple] = None
    ) -> List[str]:
        """Capture timelapse sequence.
        
        Args:
            output_dir: Directory to save frames
            interval: Seconds between frames
            duration: Total duration in seconds
            resolution: Optional (width, height) tuple
        
        Returns:
            List of captured image paths
        """
        import time
        
        if not self.enabled or not self.camera:
            return []
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        captured_files = []
        start_time = time.time()
        frame_count = 0
        
        try:
            while time.time() - start_time < duration:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                frame_path = output_path / f"frame_{frame_count:05d}_{timestamp}.jpg"
                
                photo_path = self.capture_photo(str(frame_path), resolution)
                if photo_path:
                    captured_files.append(photo_path)
                
                frame_count += 1
                time.sleep(interval)
            
            logger.info(f"Timelapse captured: {len(captured_files)} frames")
            return captured_files
            
        except Exception as e:
            logger.error(f"Failed to capture timelapse: {e}", exc_info=True)
            return captured_files
    
    def cleanup(self):
        """Cleanup camera resources."""
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
            except Exception as e:
                logger.error(f"Failed to cleanup camera: {e}")
            self.camera = None
    
    def __del__(self):
        """Destructor - cleanup on deletion."""
        self.cleanup()
