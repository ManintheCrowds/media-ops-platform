"""GPIO interface for sensor reading and device control."""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import GPIO libraries, but handle gracefully if not available
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    try:
        from gpiozero import Device, DigitalInputDevice, DigitalOutputDevice, LED, Button
        GPIO_AVAILABLE = True
        GPIO_LIBRARY = "gpiozero"
    except ImportError:
        GPIO_AVAILABLE = False
        GPIO_LIBRARY = None
        logger.warning("GPIO libraries not available. GPIO functionality will be disabled.")


class PinMode(str, Enum):
    """GPIO pin modes."""
    INPUT = "input"
    OUTPUT = "output"
    PWM = "pwm"


class GPIOInterface:
    """Interface for GPIO operations."""
    
    def __init__(self, enabled: bool = True):
        """Initialize GPIO interface."""
        self.enabled = enabled and GPIO_AVAILABLE
        self._pins: Dict[int, Any] = {}
        self._sensors: Dict[str, Any] = {}
        
        if self.enabled:
            try:
                if GPIO_LIBRARY == "gpiozero":
                    # gpiozero doesn't need explicit setup
                    pass
                else:
                    GPIO.setmode(GPIO.BCM)
                    GPIO.setwarnings(False)
            except Exception as e:
                logger.error(f"Failed to initialize GPIO: {e}")
                self.enabled = False
    
    def setup_pin(self, pin: int, mode: PinMode, initial: Optional[bool] = None):
        """Setup a GPIO pin."""
        if not self.enabled:
            logger.warning("GPIO is disabled")
            return False
        
        try:
            if GPIO_LIBRARY == "gpiozero":
                if mode == PinMode.INPUT:
                    device = DigitalInputDevice(pin)
                elif mode == PinMode.OUTPUT:
                    device = DigitalOutputDevice(pin, initial_value=initial)
                else:
                    logger.warning(f"PWM mode not yet implemented with gpiozero")
                    return False
                self._pins[pin] = device
            else:
                gpio_mode = GPIO.IN if mode == PinMode.INPUT else GPIO.OUT
                GPIO.setup(pin, gpio_mode, initial=initial)
                self._pins[pin] = {"mode": mode, "initial": initial}
            
            return True
        except Exception as e:
            logger.error(f"Failed to setup pin {pin}: {e}")
            return False
    
    def read_pin(self, pin: int) -> Optional[bool]:
        """Read digital pin value."""
        if not self.enabled or pin not in self._pins:
            return None
        
        try:
            if GPIO_LIBRARY == "gpiozero":
                device = self._pins[pin]
                if isinstance(device, DigitalInputDevice):
                    return device.value
                return None
            else:
                return GPIO.input(pin) == GPIO.HIGH
        except Exception as e:
            logger.error(f"Failed to read pin {pin}: {e}")
            return None
    
    def write_pin(self, pin: int, value: bool):
        """Write digital pin value."""
        if not self.enabled or pin not in self._pins:
            return False
        
        try:
            if GPIO_LIBRARY == "gpiozero":
                device = self._pins[pin]
                if isinstance(device, DigitalOutputDevice):
                    device.value = value
                    return True
                return False
            else:
                GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)
                return True
        except Exception as e:
            logger.error(f"Failed to write pin {pin}: {e}")
            return False
    
    def read_sensor(self, sensor_type: str, pin: Optional[int] = None) -> Optional[float]:
        """Read sensor value.
        
        Args:
            sensor_type: Type of sensor (temperature, humidity, etc.)
            pin: Optional GPIO pin number
        
        Returns:
            Sensor value or None if unavailable
        """
        if not self.enabled:
            return None
        
        # This is a placeholder - actual sensor reading would depend on the sensor hardware
        # For example, DHT22 temperature/humidity sensor, DS18B20 temperature sensor, etc.
        logger.debug(f"Reading {sensor_type} sensor on pin {pin}")
        
        # Mock implementation - would be replaced with actual sensor reading
        if sensor_type == "temperature":
            # Would read from actual sensor
            return 22.5
        elif sensor_type == "humidity":
            return 45.0
        
        return None
    
    def control_led(self, pin: int, state: bool):
        """Control an LED."""
        return self.write_pin(pin, state)
    
    def read_button(self, pin: int) -> Optional[bool]:
        """Read button state."""
        return self.read_pin(pin)
    
    def cleanup(self):
        """Cleanup GPIO resources."""
        if self.enabled and GPIO_LIBRARY != "gpiozero":
            try:
                GPIO.cleanup()
            except Exception as e:
                logger.error(f"Failed to cleanup GPIO: {e}")
        
        self._pins.clear()
        self._sensors.clear()
    
    def __del__(self):
        """Destructor - cleanup on deletion."""
        self.cleanup()







