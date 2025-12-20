"""Power management for battery monitoring and optimization."""

import logging
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class PowerManager:
    """Manages power state and battery monitoring."""
    
    def __init__(self):
        """Initialize power manager."""
        self._battery_path = Path("/sys/class/power_supply/BAT0")
        self._ac_path = Path("/sys/class/power_supply/AC")
    
    def get_battery_level(self) -> Optional[float]:
        """Get battery level as percentage (0.0 to 100.0).
        
        Returns:
            Battery percentage or None if not available
        """
        try:
            capacity_file = self._battery_path / "capacity"
            if capacity_file.exists():
                with open(capacity_file, "r") as f:
                    return float(f.read().strip())
        except Exception as e:
            logger.debug(f"Could not read battery level: {e}")
        
        return None
    
    def is_charging(self) -> Optional[bool]:
        """Check if device is charging.
        
        Returns:
            True if charging, False if not, None if unknown
        """
        try:
            status_file = self._battery_path / "status"
            if status_file.exists():
                with open(status_file, "r") as f:
                    status = f.read().strip().upper()
                    return status == "CHARGING"
        except Exception as e:
            logger.debug(f"Could not read charging status: {e}")
        
        return None
    
    def is_ac_connected(self) -> Optional[bool]:
        """Check if AC power is connected.
        
        Returns:
            True if AC connected, False if not, None if unknown
        """
        try:
            if self._ac_path.exists():
                online_file = self._ac_path / "online"
                if online_file.exists():
                    with open(online_file, "r") as f:
                        return f.read().strip() == "1"
        except Exception as e:
            logger.debug(f"Could not read AC status: {e}")
        
        return None
    
    def get_power_info(self) -> Dict[str, Any]:
        """Get comprehensive power information.
        
        Returns:
            Dictionary with power state information
        """
        info = {
            "battery_level": self.get_battery_level(),
            "is_charging": self.is_charging(),
            "is_ac_connected": self.is_ac_connected(),
        }
        
        # Try to get voltage if available
        try:
            voltage_file = self._battery_path / "voltage_now"
            if voltage_file.exists():
                with open(voltage_file, "r") as f:
                    voltage_uv = int(f.read().strip())
                    info["voltage_v"] = voltage_uv / 1_000_000
        except Exception:
            pass
        
        # Try to get current if available
        try:
            current_file = self._battery_path / "current_now"
            if current_file.exists():
                with open(current_file, "r") as f:
                    current_ua = int(f.read().strip())
                    info["current_ma"] = current_ua / 1_000
        except Exception:
            pass
        
        return info
    
    def optimize_for_battery(self):
        """Apply power optimizations for battery operation."""
        logger.info("Applying battery optimizations...")
        
        # Reduce CPU frequency
        try:
            # Set CPU governor to powersave
            subprocess.run(
                ["sudo", "cpufreq-set", "-g", "powersave"],
                check=False,
                capture_output=True
            )
        except Exception:
            pass
        
        # Disable unnecessary services (would be implemented based on requirements)
        logger.info("Battery optimizations applied")
    
    def optimize_for_performance(self):
        """Apply performance optimizations (when on AC power)."""
        logger.info("Applying performance optimizations...")
        
        # Set CPU governor to performance
        try:
            subprocess.run(
                ["sudo", "cpufreq-set", "-g", "performance"],
                check=False,
                capture_output=True
            )
        except Exception:
            pass
        
        logger.info("Performance optimizations applied")
    
    def should_sleep(self) -> bool:
        """Determine if device should enter sleep mode.
        
        Returns:
            True if device should sleep
        """
        battery_level = self.get_battery_level()
        is_charging = self.is_charging()
        is_ac = self.is_ac_connected()
        
        # Sleep if battery is low and not charging/plugged in
        if battery_level is not None and battery_level < 10:
            if not (is_charging or is_ac):
                return True
        
        return False



