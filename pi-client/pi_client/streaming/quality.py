"""Adaptive quality management for streaming."""

import logging
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class QualityLevel(str, Enum):
    """Quality levels for streaming."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    AUTO = "auto"


class QualityManager:
    """Manages adaptive quality selection based on network conditions."""
    
    def __init__(self):
        """Initialize quality manager."""
        self.current_quality = QualityLevel.AUTO
        self.network_speed_mbps = 0.0
        self.buffer_health = 1.0  # 0.0 to 1.0
        self._quality_history: list[float] = []
    
    def update_network_speed(self, speed_mbps: float):
        """Update measured network speed."""
        self.network_speed_mbps = speed_mbps
        self._quality_history.append(speed_mbps)
        # Keep only last 10 measurements
        if len(self._quality_history) > 10:
            self._quality_history.pop(0)
    
    def update_buffer_health(self, health: float):
        """Update buffer health (0.0 = empty, 1.0 = full)."""
        self.buffer_health = max(0.0, min(1.0, health))
    
    def get_recommended_quality(self) -> QualityLevel:
        """Get recommended quality level based on current conditions."""
        if self.current_quality != QualityLevel.AUTO:
            return self.current_quality
        
        # Calculate average network speed
        avg_speed = (
            sum(self._quality_history) / len(self._quality_history)
            if self._quality_history
            else self.network_speed_mbps
        )
        
        # Adjust quality based on network speed and buffer health
        if avg_speed < 2.0 or self.buffer_health < 0.2:
            return QualityLevel.LOW
        elif avg_speed < 5.0 or self.buffer_health < 0.5:
            return QualityLevel.MEDIUM
        else:
            return QualityLevel.HIGH
    
    def set_quality(self, quality: QualityLevel):
        """Manually set quality level."""
        self.current_quality = quality
        logger.info(f"Quality set to {quality.value}")
    
    def get_quality_params(self, quality: Optional[QualityLevel] = None) -> Dict[str, Any]:
        """Get quality parameters for a quality level."""
        quality = quality or self.get_recommended_quality()
        
        params = {
            QualityLevel.LOW: {
                "bitrate": "500k",
                "resolution": "640x360",
                "chunk_size": 512 * 1024,  # 512KB chunks
            },
            QualityLevel.MEDIUM: {
                "bitrate": "1500k",
                "resolution": "1280x720",
                "chunk_size": 1024 * 1024,  # 1MB chunks
            },
            QualityLevel.HIGH: {
                "bitrate": "3000k",
                "resolution": "1920x1080",
                "chunk_size": 2 * 1024 * 1024,  # 2MB chunks
            },
        }
        
        return params.get(quality, params[QualityLevel.MEDIUM])

