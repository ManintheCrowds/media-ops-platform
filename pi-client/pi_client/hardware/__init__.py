"""Hardware integration module."""

from .gpio import GPIOInterface
from .camera import CameraInterface
from .audio import AudioManager
from .power import PowerManager

__all__ = ["GPIOInterface", "CameraInterface", "AudioManager", "PowerManager"]




