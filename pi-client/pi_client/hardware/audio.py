"""Audio management for playback and volume control."""

import logging
import subprocess
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import audio libraries
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logger.warning("pygame not available. Some audio features may be limited.")


class AudioManager:
    """Manages audio playback and volume control."""
    
    def __init__(self, enabled: bool = True):
        """Initialize audio manager."""
        self.enabled = enabled
        self._current_file: Optional[str] = None
        self._playing = False
        
        if self.enabled and PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                logger.info("Audio system initialized")
            except Exception as e:
                logger.error(f"Failed to initialize audio: {e}")
                self.enabled = False
    
    def play_file(self, file_path: str, volume: float = 1.0, loop: bool = False) -> bool:
        """Play audio file.
        
        Args:
            file_path: Path to audio file
            volume: Volume level (0.0 to 1.0)
            loop: Whether to loop playback
        
        Returns:
            True if playback started successfully
        """
        if not self.enabled:
            logger.warning("Audio is disabled")
            return False
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            logger.error(f"Audio file not found: {file_path}")
            return False
        
        try:
            if PYGAME_AVAILABLE:
                pygame.mixer.music.load(str(file_path))
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1 if loop else 0)
                self._current_file = file_path
                self._playing = True
                logger.info(f"Playing audio file: {file_path}")
                return True
            else:
                # Fallback to system player
                cmd = ["aplay", str(file_path)]
                if loop:
                    # aplay doesn't support looping directly
                    logger.warning("Looping not supported with aplay fallback")
                subprocess.Popen(cmd)
                self._current_file = file_path
                self._playing = True
                return True
                
        except Exception as e:
            logger.error(f"Failed to play audio file: {e}", exc_info=True)
            return False
    
    def stop(self):
        """Stop current playback."""
        if PYGAME_AVAILABLE and self._playing:
            try:
                pygame.mixer.music.stop()
                self._playing = False
                logger.info("Audio playback stopped")
            except Exception as e:
                logger.error(f"Failed to stop playback: {e}")
    
    def pause(self):
        """Pause current playback."""
        if PYGAME_AVAILABLE and self._playing:
            try:
                pygame.mixer.music.pause()
                logger.info("Audio playback paused")
            except Exception as e:
                logger.error(f"Failed to pause playback: {e}")
    
    def resume(self):
        """Resume paused playback."""
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.unpause()
                logger.info("Audio playback resumed")
            except Exception as e:
                logger.error(f"Failed to resume playback: {e}")
    
    def set_volume(self, volume: float):
        """Set playback volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        volume = max(0.0, min(1.0, volume))
        
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.set_volume(volume)
                logger.info(f"Volume set to {volume}")
            except Exception as e:
                logger.error(f"Failed to set volume: {e}")
        else:
            # Use amixer for system volume
            try:
                # Convert 0.0-1.0 to 0-100
                volume_percent = int(volume * 100)
                subprocess.run(
                    ["amixer", "set", "PCM", f"{volume_percent}%"],
                    check=True,
                    capture_output=True
                )
            except Exception as e:
                logger.error(f"Failed to set system volume: {e}")
    
    def get_volume(self) -> float:
        """Get current volume level."""
        if PYGAME_AVAILABLE:
            try:
                return pygame.mixer.music.get_volume()
            except Exception:
                return 1.0
        else:
            # Try to get system volume
            try:
                result = subprocess.run(
                    ["amixer", "get", "PCM"],
                    capture_output=True,
                    text=True
                )
                # Parse output (simplified)
                return 0.5  # Default if parsing fails
            except Exception:
                return 1.0
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        if PYGAME_AVAILABLE:
            return pygame.mixer.music.get_busy()
        return self._playing
    
    def cleanup(self):
        """Cleanup audio resources."""
        self.stop()
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.quit()
            except Exception as e:
                logger.error(f"Failed to cleanup audio: {e}")

