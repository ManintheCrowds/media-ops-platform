"""Enums for camera models."""

from enum import Enum


class ArloStatus(Enum):
    """Arlo camera status enum."""
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"
    BATTERY_LOW = "battery_low"
    WEAK_SIGNAL = "weak_signal"


class ArloEventType(Enum):
    """Arlo event type enum."""
    MOTION = "motion"
    AUDIO = "audio"
    BATTERY_LOW = "battery_low"
    OFFLINE = "offline"
    ONLINE = "online"
    RECORDING_STARTED = "recording_started"
    RECORDING_COMPLETED = "recording_completed"
    SNAPSHOT_CAPTURED = "snapshot_captured"

