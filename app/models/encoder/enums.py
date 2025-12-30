"""Enums for encoder models."""

from enum import Enum


class EncoderStatus(Enum):
    """Video encoder status enum."""
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"
    ERROR = "error"
    RECORDING = "recording"
    STREAMING = "streaming"


class EncoderDeviceType(Enum):
    """Encoder device type enum."""
    AJA_HELO = "aja_helo"
    GENERIC = "generic"

